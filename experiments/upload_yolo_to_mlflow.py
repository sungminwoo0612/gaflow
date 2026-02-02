"""
yolo11n.pt(또는 지정 .pt)를 MLflow Models에 업로드.
추론 없이 모델만 등록할 때 사용.

사용:
  python experiments/upload_yolo_to_mlflow.py
  python experiments/upload_yolo_to_mlflow.py --model path/to/yolo11n.pt
"""
import argparse
from pathlib import Path

import mlflow
from ultralytics import YOLO

EXPERIMENT_NAME = "yolo-video-inference"
REGISTERED_MODEL_NAME = "yolo-video-inference"


def _resolve_pt_path(model_weight: str) -> Path | None:
    """로컬 .pt 파일 경로 반환. 없으면 None."""
    p = Path(model_weight)
    if p.exists():
        return p.resolve()
    # Ultralytics가 현재 디렉터리에 다운로드한 경우
    cwd = Path.cwd()
    if (cwd / model_weight).exists():
        return (cwd / model_weight).resolve()
    if p.is_absolute():
        return None
    if (cwd / p).exists():
        return (cwd / p).resolve()
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description="YOLO .pt를 MLflow Models에 업로드")
    parser.add_argument(
        "--model",
        type=str,
        default="yolo11n.pt",
        help="모델 파일 경로 또는 이름 (기본: yolo11n.pt)",
    )
    parser.add_argument(
        "--registered-name",
        type=str,
        default=REGISTERED_MODEL_NAME,
        help="등록할 모델 이름",
    )
    args = parser.parse_args()
    model_weight = args.model
    registered_name = args.registered_name

    mlflow.set_experiment(EXPERIMENT_NAME)
    run_name = f"upload-{Path(model_weight).stem}"

    with mlflow.start_run(run_name=run_name):
        mlflow.log_param("model_weight", model_weight)
        mlflow.set_tag("task", "upload_model")

        print(f"📦 로드 중: {model_weight}")
        model = YOLO(model_weight)

        # .pt 파일을 아티팩트로 로깅 (경로를 찾을 수 있을 때)
        pt_path = _resolve_pt_path(model_weight)
        if pt_path is not None and pt_path.exists():
            mlflow.log_artifact(str(pt_path), "weights")
            mlflow.log_param("weights_artifact", str(pt_path.name))
            print(f"✅ 아티팩트 로깅: weights/{pt_path.name}")
        else:
            print(f"⚠️ 로컬 .pt 경로를 찾지 못함. PyTorch 모델만 등록합니다.")

        # PyTorch 모델로 Models에 등록
        mlflow.pytorch.log_model(
            model.model,
            "model",
            registered_model_name=registered_name,
        )
        print(f"✅ Models 등록: {registered_name}")

    print("끝. MLflow UI > Models에서 확인하세요.")


if __name__ == "__main__":
    main()
