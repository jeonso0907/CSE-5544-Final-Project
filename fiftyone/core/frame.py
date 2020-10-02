"""
Video frames.

| Copyright 2017-2020, Voxel51, Inc.
| `voxel51.com <https://voxel51.com/>`_
|
"""
from collections import defaultdict
import weakref


from pymongo import ReplaceOne


import fiftyone.core.frame_utils as fofu
from fiftyone.core._sample import _Sample

from fiftyone.core.odm.frame import (
    NoDatasetFrameSampleDocument,
    DatasetFrameSampleDocument,
)


#
# This class is instantiated automatically and depends on an owning
# :class:`fiftyone.core.sample.Sample`. Not for independent use or direct
# assignment to :class:`fiftyone.core.sample.Sample`s.
#
class Frames(object):
    """An ordered dictionary of labels for the frames of a
    :class:`fiftyone.core.sample.Sample`.

    The frame labels are stored in :class:`Frame` instances.

    :class:`Frames` instances behave like ``defaultdict(Frame)`` instances; an
    empty :class:`Frame` instance is returned when accessing a new frame
    number.
    """

    def __init__(self):
        self._sample = None
        self._iter = None
        self._replacements = {}
        self._cache = {}

    def __repr__(self):
        num_frames = len(self)
        plural = "s" if num_frames != 1 else ""
        return "{ <%d frame%s> }" % (num_frames, plural)

    def __len__(self):
        return self._sample._doc.frames["frame_count"]

    def _set_replacement(self, d):
        self._replacements[d["frame_number"]] = d

    def _save_replacements(self):
        self._frame_collection.bulk_write(
            [
                ReplaceOne(self._make_filter(d), d, upsert=True)
                for d in self._replacements.values()
            ]
        )

    def _make_filter(self, d):
        return {k: d[k] for k in ["sample_id", "frame_number"]}

    def __iter__(self):
        self._iter = self.keys()
        return self

    def __next__(self):
        return next(self._iter)

    def __getitem__(self, key):
        fofu.validate_frame_number(key)

        d = None
        if key in self._replacements:
            d = self._replacements[key]
        elif self._sample._in_db:
            d = {"sample_id": self._sample.id, "frame_number": key}
            if key == 1:
                first_frame = self._sample._doc.frames["first_frame"]
                if first_frame is not None:
                    d = first_frame
            else:
                d = self._frame_collection.find_one(d)

        if d is None:
            self._set_replacement(d)
            self._sample._doc.frames["frame_count"] += 1

        if key != 1 and self._sample._in_db:
            doc = self._sample._dataset._frame_doc_cls.from_dict(d)
            dataset = self._sample._dataset
        else:
            doc = NoDatasetFrameSampleDocument(**d)
            dataset = None

        return Frame.from_doc(doc, dataset=dataset)

    def __setitem__(self, key, value):
        fofu.validate_frame_number(key)

        if not isinstance(value, Frame):
            raise ValueError("Value must be a %s" % Frame.__name__)

        d = value.to_dict()
        d["frame_number"] = key
        d["sample_id"] = self._sample.id

        d.pop("_id", None)
        self._set_replacement(d)

    def keys(self):
        """Returns an iterator over the frame numbers with labels in the
        sample.

        The frames are traversed in ascending order.

        Returns:
            a generator that emits frame numbers
        """
        for doc in self._iter_docs():
            yield doc.frame_number

    def items(self):
        """Returns an iterator over the frame numberes and :class:`Frame`
        instances for the sample.

        The frames are traversed in ascending order.

        Returns:
            a generator that emits ``(frame_number, Frame)`` tuples
        """
        for doc in self._iter_docs():
            yield doc.frame_number, Frame.from_doc(
                doc, dataset=self._sample._dataset
            )

    def values(self):
        """Returns an iterator over the :class:`Frame` instances for the
        sample.

        The frames are traversed in ascending order.

        Returns:
            a generator that emits :class:`Frame` instances
        """
        dataset = self._sample._dataset if self._sample._in_db else None
        for doc in self._iter_docs():
            yield Frame.from_doc(doc, dataset=self._sample._dataset)

    def update(self, d):
        """Adds the frame labels from the given dictionary to this instance.

        Existing frames are overwritten.

        Args:
            d: a dictionary mapping frame numbers to :class:`Frame` instances
        """
        for frame_number, frame in d.items():
            self[frame_number] = frame

    @property
    def _first_frame(self):
        first_frame = self._replacements.get(1, None)
        if first_frame is None and self._sample._in_db:
            return self._sample._doc.frames["first_frame"]

    def to_mongo_dict(self):
        first_frame = self._first_frame
        if first_frame:
            first_frame = first_frame.to_mongo_dict()
        return {
            "frame_count": self._sample._doc.frames["frame_count"],
            "first_frame": first_frame,
        }

    def _expand_schema(self, dataset):
        pass

    @property
    def _frame_collection(self):
        return self._sample._dataset._frame_collection

    def _iter_docs(self):
        if self._sample._in_db:
            self._save()
            if 1 in self._replacements:
                yield self._replacements[1]
            elif self._sample._doc.frames.first_frame:
                yield self._sample._doc.frames.first_frame

            repl_fns = sorted(self._replacements.keys())
            repl_fn = repl_fns[0] if len(repl_fns) else None
            for d in self._frame_collection.find(
                {"sample_id": self._sample.id}
            ):
                if d["frame_number"] >= repl_fn:
                    yield self._replacements[repl_fn]
                    repl_fn += 1
                else:
                    yield self._sample._dataset._frame_dict_to_doc(d)
        else:
            for frame_number in sorted(self._replacements.keys()):
                yield self._replacements[frame_number]

    def _get_field_cls(self):
        return self._sample._doc.frames.__class__

    def _save(self):
        if not self._sample._in_db:
            raise fofu.FrameError(
                "Sample does not have a dataset, Frames cannot be saved"
            )
        if 1 in self._replacements:
            raise fofu.FrameError("Sample has not been saved yet")
        self._save_replacements()

    def _serve(self, sample):
        self._sample = sample
        return self


class Frame(_Sample):
    """A frame in a video :class:`fiftyone.core.sample.Sample`.

    :class:`Frame` instances can hold any :class:`fiftyone.core.label.Label`
    or other :class:`fiftyone.core.fields.Field` type that can be assigned
    directly to :class:`fiftyone.core.sample.Sample` instances.
    """

    # Instance references keyed by [collection_name][sample_id]
    _instances = defaultdict(weakref.WeakValueDictionary)

    _COLL_CLS = DatasetFrameSampleDocument
    _NO_COLL_CLS = NoDatasetFrameSampleDocument

    def __init__(self, **kwargs):
        self._doc = NoDatasetFrameSampleDocument(**kwargs)
        super().__init__()

    def __str__(self):
        return repr(self)

    def __repr__(self):
        return self._doc.fancy_repr(class_name=self.__class__.__name__)

    def __getitem__(self, field_name):
        try:
            return self.get_field(field_name)
        except AttributeError:
            raise KeyError(
                "%s has no field '%s'" % (self.__class__.__name__, field_name)
            )

    def __setitem__(self, field_name, value):
        self.set_field(field_name, value=value)

    @classmethod
    def from_doc(cls, doc, dataset=None):
        """Creates an instance of the :class:`Frame` class backed by the given
        document.

        Args:
            doc: a :class:`fiftyone.core.odm.SampleDocument`
            dataset (None): the :class:`fiftyone.core.dataset.Dataset` that the
                frame belongs to

        Returns:
            a :class:`Frame`
        """
        if isinstance(doc, NoDatasetFrameSampleDocument):
            sample = cls.__new__(cls)
            sample._dataset = None
            sample._doc = doc
            return sample

        if not doc.id:
            raise ValueError("`doc` is not saved to the database.")

        try:
            # Get instance if exists
            sample = cls._instances[doc.collection_name][str(doc.id)]
        except KeyError:
            sample = cls.__new__(cls)
            sample._doc = None  # set to prevent RecursionError
            if dataset is None:
                raise ValueError(
                    "`dataset` arg must be provided if sample is in a dataset"
                )
            sample._set_backing_doc(doc, dataset=dataset)

        return sample
