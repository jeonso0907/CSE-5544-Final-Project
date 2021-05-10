"""
Documents that track datasets and their sample schemas in the database.

| Copyright 2017-2021, Voxel51, Inc.
| `voxel51.com <https://voxel51.com/>`_
|
"""
import inspect

import eta.core.utils as etau

from fiftyone.core.fields import (
    Field,
    BooleanField,
    ClassesField,
    DictField,
    EmbeddedDocumentField,
    EmbeddedDocumentListField,
    ListField,
    StringField,
    TargetsField,
)

from .document import Document, EmbeddedDocument, BaseEmbeddedDocument
from .runs import RunDocument


def create_field(field_name, ftype, embedded_doc_type=None, subfield=None):
    """Creates the :class:`fiftyone.core.fields.Field` instance defined by the
    given specification.

    Args:
        field_name: the field name
        ftype: the field type to create. Must be a subclass of
            :class:`fiftyone.core.fields.Field`
        embedded_doc_type (None): the
            :class:`fiftyone.core.odm.BaseEmbeddedDocument` type of the field.
            Only applicable when ``ftype`` is
            :class:`fiftyone.core.fields.EmbeddedDocumentField`
        subfield (None): the :class:`fiftyone.core.fields.Field` type of the
            contained field. Only applicable when ``ftype`` is
            :class:`fiftyone.core.fields.ListField` or
            :class:`fiftyone.core.fields.DictField`

    Returns:
        a :class:`fiftyone.core.fields.Field` instance
    """
    if not issubclass(ftype, Field):
        raise ValueError(
            "Invalid field type %s; must be a subclass of %s" % (ftype, Field)
        )

    kwargs = dict(db_field=field_name, null=True)

    if issubclass(ftype, EmbeddedDocumentField):
        if not issubclass(embedded_doc_type, BaseEmbeddedDocument):
            raise ValueError(
                "Invalid embedded_doc_type %s; must be a subclass of %s"
                % (embedded_doc_type, BaseEmbeddedDocument)
            )

        kwargs.update({"document_type": embedded_doc_type})
    elif issubclass(ftype, (ListField, DictField)):
        if subfield is not None:
            if inspect.isclass(subfield):
                subfield = subfield()

            if not isinstance(subfield, Field):
                raise ValueError(
                    "Invalid subfield type %s; must be a subclass of %s"
                    % (type(subfield), Field)
                )

            kwargs["field"] = subfield

    field = ftype(**kwargs)
    field.name = field_name

    return field


class SampleFieldDocument(EmbeddedDocument):
    """Description of a sample field."""

    name = StringField()
    ftype = StringField()
    subfield = StringField(null=True)
    embedded_doc_type = StringField(null=True)

    def to_field(self):
        """Creates the :class:`fiftyone.core.fields.Field` specified by this
        document.

        Returns:
            a :class:`fiftyone.core.fields.Field`
        """
        ftype = etau.get_class(self.ftype)

        embedded_doc_type = self.embedded_doc_type
        if embedded_doc_type is not None:
            embedded_doc_type = etau.get_class(embedded_doc_type)

        subfield = self.subfield
        if subfield is not None:
            subfield = etau.get_class(subfield)()

        return create_field(
            self.name,
            ftype,
            embedded_doc_type=embedded_doc_type,
            subfield=subfield,
        )

    @classmethod
    def from_field(cls, field):
        """Creates a :class:`SampleFieldDocument` for a field.

        Args:
            field: a :class:`fiftyone.core.fields.Field` instance

        Returns:
            a :class:`SampleFieldDocument`
        """
        return cls(
            name=field.name,
            ftype=etau.get_class_name(field),
            subfield=cls._get_attr_repr(field, "field"),
            embedded_doc_type=cls._get_attr_repr(field, "document_type"),
        )

    @classmethod
    def list_from_field_schema(cls, d):
        """Creates a list of :class:`SampleFieldDocument` objects from a field
        schema.

        Args:
             d: a dict generated by
                :func:`fiftyone.core.dataset.Dataset.get_field_schema`

        Returns:
             a list of :class:`SampleFieldDocument` objects
        """
        return [cls.from_field(field) for field in d.values()]

    def matches_field(self, field):
        """Determines whether this sample field matches the given field.

        Args:
            field: a :class:`fiftyone.core.fields.Field` instance

        Returns:
            True/False
        """
        if self.name != field.name:
            return False

        if self.ftype != etau.get_class_name(field):
            return False

        if self.subfield and self.subfield != etau.get_class_name(field.field):
            return False

        if (
            self.embedded_doc_type
            and self.embedded_doc_type
            != etau.get_class_name(field.document_type)
        ):
            return False

        return True

    @staticmethod
    def _get_attr_repr(field, attr_name):
        attr = getattr(field, attr_name, None)
        return etau.get_class_name(attr) if attr else None


class DatasetDocument(Document):
    """Backing document for datasets."""

    meta = {"collection": "datasets"}

    media_type = StringField()
    name = StringField(unique=True, required=True)
    sample_collection_name = StringField(unique=True, required=True)
    persistent = BooleanField(default=False)
    info = DictField()
    evaluations = DictField(EmbeddedDocumentField(document_type=RunDocument))
    brain_methods = DictField(EmbeddedDocumentField(document_type=RunDocument))
    sample_fields = EmbeddedDocumentListField(
        document_type=SampleFieldDocument
    )
    frame_fields = EmbeddedDocumentListField(document_type=SampleFieldDocument)
    classes = DictField(ClassesField())
    default_classes = ClassesField()
    mask_targets = DictField(TargetsField())
    default_mask_targets = TargetsField()
    version = StringField(required=True, null=True)
