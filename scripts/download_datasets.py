import kagglehub
from kagglehub.exceptions import KaggleApiHTTPError

dataset_slugs = [
    "tudorhirtopanu/yolo-highvis-and-person-detection-dataset",
    "solesensei/solesensei_bdd100k",
    "sakshamjn/vehicle-detection-8-classes-object-detection",
]

# Download latest version
for dataset_slug in dataset_slugs:
    try:
        path = kagglehub.dataset_download(dataset_slug)
        print(f"Path to dataset files: {path}")
    except KaggleApiHTTPError as e:
        print(f"Skip {dataset_slug}: {e}")
    print(f"Path to dataset files: {path}")
