"""
실험 2: 다양한 하이퍼파라미터로 YOLO 모델 학습
"""
import mlflow
import mlflow.ultralytics
from ultralytics import YOLO
from pathlib import Path
import sys

# MLflow 실험 설정
mlflow.set_experiment("yolo-hyperparams")

# 파라미터 파싱 (MLproject에서 환경 변수로 전달됨)
import os
epochs = int(os.getenv("epochs", "10"))
batch_size = int(os.getenv("batch_size", "32"))
learning_rate = float(os.getenv("learning_rate", "0.01"))
model_size = os.getenv("model_size", "yolov8s")

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = BASE_DIR / "datasets" / "coco8" / "coco8.yaml"

with mlflow.start_run(run_name=f"hyperparams-{model_size}-lr{learning_rate}-e{epochs}"):
    # 파라미터 로깅
    mlflow.log_params({
        "epochs": epochs,
        "batch_size": batch_size,
        "learning_rate": learning_rate,
        "model_size": model_size,
        "experiment_type": "hyperparams",
        "optimizer": "AdamW",
        "momentum": 0.937,
        "weight_decay": 0.0005
    })
    
    # 모델 초기화
    model = YOLO(f"{model_size}.pt")
    
    # MLflow 자동 로깅 활성화
    mlflow.ultralytics.autolog()
    
    # 학습 (하이퍼파라미터 튜닝)
    results = model.train(
        data=str(DATA_PATH),
        epochs=epochs,
        batch=batch_size,
        lr0=learning_rate,
        imgsz=640,
        optimizer="AdamW",
        momentum=0.937,
        weight_decay=0.0005,
        project=str(BASE_DIR / "mlflow_runs"),
        name="hyperparams"
    )
    
    # 검증
    val_results = model.val()
    
    # 메트릭 로깅
    mlflow.log_metrics({
        "train/box_loss": results.results_dict.get("train/box_loss", 0),
        "train/cls_loss": results.results_dict.get("train/cls_loss", 0),
        "train/dfl_loss": results.results_dict.get("train/dfl_loss", 0),
        "val/mAP50": val_results.results_dict.get("metrics/mAP50(B)", 0),
        "val/mAP50-95": val_results.results_dict.get("metrics/mAP50-95(B)", 0),
        "val/precision": val_results.results_dict.get("metrics/precision(B)", 0),
        "val/recall": val_results.results_dict.get("metrics/recall(B)", 0),
    })
    
    # 모델 저장
    model_path = BASE_DIR / "mlflow_runs" / "hyperparams" / "weights" / "best.pt"
    if model_path.exists():
        mlflow.log_artifact(str(model_path), "model")
    
    print(f"✅ Hyperparams experiment completed: {model_size}, lr={learning_rate}, epochs={epochs}")
