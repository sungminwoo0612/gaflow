"""
실험 1: 기본 파라미터로 YOLO 모델 학습
"""
import mlflow
import mlflow.ultralytics
from ultralytics import YOLO
from pathlib import Path
import sys

# MLflow 실험 설정
mlflow.set_experiment("yolo-baseline")

# 파라미터 파싱 (MLproject에서 환경 변수로 전달됨)
import os
epochs = int(os.getenv("epochs", "5"))
batch_size = int(os.getenv("batch_size", "16"))
model_size = os.getenv("model_size", "yolov8n")

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = BASE_DIR / "datasets" / "coco8" / "coco8.yaml"
# Ultralytics는 상대 경로나 절대 경로 모두 지원
# 프로젝트 루트에서 실행되므로 상대 경로 사용

with mlflow.start_run(run_name=f"baseline-{model_size}-e{epochs}"):
    # 파라미터 로깅
    mlflow.log_params({
        "epochs": epochs,
        "batch_size": batch_size,
        "model_size": model_size,
        "experiment_type": "baseline"
    })
    
    # 모델 초기화
    model = YOLO(f"{model_size}.pt")
    
    # MLflow 자동 로깅 활성화
    mlflow.ultralytics.autolog()
    
    # 학습
    results = model.train(
        data=str(DATA_PATH),
        epochs=epochs,
        batch=batch_size,
        imgsz=640,
        project=str(BASE_DIR / "mlflow_runs"),
        name="baseline"
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
    model_path = BASE_DIR / "mlflow_runs" / "baseline" / "weights" / "best.pt"
    if model_path.exists():
        mlflow.log_artifact(str(model_path), "model")
    
    print(f"✅ Baseline experiment completed: {model_size}, epochs={epochs}")
