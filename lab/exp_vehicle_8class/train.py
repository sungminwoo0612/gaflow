"""
YOLO 실험: Vehicle 8-class (sakshamjn/vehicle-detection-8-classes-object-detection)
"""
import os
from pathlib import Path

import mlflow
from ultralytics import YOLO


def _resolve_data_yaml(data_path: str, base_dir: Path) -> Path:
    p = Path(data_path)
    if not p.is_absolute():
        p = (base_dir / p).resolve()
    if p.suffix.lower() in (".yaml", ".yml"):
        return p
    for name in ("data.yaml", "dataset.yaml", "train.yaml"):
        candidate = p / name
        if candidate.exists():
            return candidate
    for f in p.rglob("*.yaml"):
        if "data" in f.stem.lower() or f.name == "dataset.yaml":
            return f
    return p / "data.yaml"


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
mlflow.set_experiment("lab-vehicle-8class")

data_path = os.getenv("data_path", "datasets/vehicle-detection-8-classes-object-detection")
epochs = int(os.getenv("epochs", "5"))
batch_size = int(os.getenv("batch_size", "16"))
model_size = os.getenv("model_size", "yolov8n")

data_yaml = _resolve_data_yaml(data_path, PROJECT_ROOT)
if not data_yaml.exists():
    raise FileNotFoundError(f"Data YAML not found: {data_yaml}. Run test.py or download_datasets.py first.")

run_name = f"vehicle8-{model_size}-e{epochs}"
project_dir = PROJECT_ROOT / "mlflow_runs" / "lab_vehicle_8class"

with mlflow.start_run(run_name=run_name):
    mlflow.log_params({
        "data_path": str(data_path),
        "epochs": epochs,
        "batch_size": batch_size,
        "model_size": model_size,
        "dataset": "vehicle-detection-8-classes",
    })
    model = YOLO(f"{model_size}.pt")
    results = model.train(
        data=str(data_yaml),
        epochs=epochs,
        batch=batch_size,
        imgsz=640,
        project=str(project_dir),
        name=run_name,
    )
    val_results = model.val()
    box = getattr(val_results, "box", None)
    map50 = getattr(box, "map50", None) if box is not None else None
    map5095 = getattr(box, "map", None) if box is not None else None
    if map50 is None:
        map50 = getattr(val_results, "results_dict", {}).get("metrics/mAP50(B)", 0)
    if map5095 is None:
        map5095 = getattr(val_results, "results_dict", {}).get("metrics/mAP50-95(B)", 0)
    mlflow.log_metrics({
        "train/box_loss": (results.results_dict or {}).get("train/box_loss", 0),
        "val/mAP50": float(map50) if map50 is not None else 0,
        "val/mAP50-95": float(map5095) if map5095 is not None else 0,
    })
    best_pt = project_dir / run_name / "weights" / "best.pt"
    if best_pt.exists():
        mlflow.log_artifact(str(best_pt), "model")
    print(f"Done: {model_size}, epochs={epochs}")
