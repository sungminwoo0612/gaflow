"""
BDD100k 데이터셋 YOLO 학습 (MLflow 통합)
데이터셋: solesensei/solesensei_bdd100k
"""
import os
from pathlib import Path
import sys

# 프로젝트 루트를 Python 경로에 추가
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from experiments.base.mlflow_yolo import train_with_mlflow, resolve_data_yaml


def main():
    # 환경 변수에서 설정 로드
    data_path = os.getenv("DATA_PATH", "datasets/solesensei/solesensei_bdd100k")
    epochs = int(os.getenv("EPOCHS", "5"))
    batch_size = int(os.getenv("BATCH_SIZE", "16"))
    model_size = os.getenv("MODEL_SIZE", "yolov8n")
    imgsz = int(os.getenv("IMGSZ", "640"))
    
    # MLflow 설정
    experiment_name = os.getenv("MLFLOW_EXPERIMENT", "lab-bdd100k")
    tracking_uri = os.getenv("MLFLOW_TRACKING_URI", None)
    
    if tracking_uri:
        import mlflow
        mlflow.set_tracking_uri(tracking_uri)
    
    # 데이터 YAML 경로 해석
    data_yaml = resolve_data_yaml(data_path, PROJECT_ROOT)
    
    if not data_yaml.exists():
        raise FileNotFoundError(
            f"Data YAML not found: {data_yaml}\n"
            f"Run download script or check DATA_PATH environment variable."
        )
    
    print(f"=== BDD100k Training Configuration ===")
    print(f"Model: {model_size}")
    print(f"Epochs: {epochs}")
    print(f"Batch Size: {batch_size}")
    print(f"Image Size: {imgsz}")
    print(f"Data YAML: {data_yaml}")
    print(f"MLflow Experiment: {experiment_name}")
    print("=" * 40)
    
    # 학습 실행
    model = train_with_mlflow(
        model_size=model_size,
        data_yaml=data_yaml,
        epochs=epochs,
        batch_size=batch_size,
        imgsz=imgsz,
        project_dir=PROJECT_ROOT / "mlflow_runs" / "lab_bdd100k",
        experiment_name=experiment_name,
        run_name=f"bdd100k-{model_size}-e{epochs}",
        extra_params={
            "dataset": "solesensei_bdd100k",
            "data_path": str(data_path),
        },
        log_model_registry=True,
        registered_model_name=f"bdd100k-detector-{model_size}",
    )
    
    print(f"\n✅ Training completed: {model_size}")
    print(f"Best weights: {model.trainer.best}")


if __name__ == "__main__":
    main()