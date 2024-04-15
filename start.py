import fiftyone as fo
import fiftyone.zoo as foz

# dataset = foz.load_zoo_dataset("quickstart")

name = 'my-kitti'
dataset_dir = 'data\kitti'
dataset = fo.Dataset.from_dir(
    dataset_dir=dataset_dir,
    dataset_type=fo.types.KITTIDetectionDataset,
    name=name,
)

if __name__ == "__main__":

    session = fo.launch_app(dataset)
    session.wait()