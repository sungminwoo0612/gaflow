"""
YOLOv11n + ByteTrack으로 영상 객체 추적 후 mp4 저장 
MLflow로 파라미터·메트릭·아티팩트 로깅
"""
import os
import subprocess
import sys
from pathlib import Path

import cv2
import mlflow
from ultralytics import YOLO

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
MLRUNS_DIR = PROJECT_ROOT / "mlruns"

VIDEO_URL = "https://www.youtube.com/watch?v=Fb1e6ytEniA"
INPUT_VIDEO: str | Path = VIDEO_URL
OUTPUT_VIDEO = SCRIPT_DIR / "output_tracked.mp4"
MODEL_WEIGHT = "yolo11n.pt"
CONF = 0.25
TRACKER = "bytetrack.yaml"
CACHE_VIDEO = SCRIPT_DIR / "input_video.mp4"

EXPERIMENT_NAME = "yolo-bytetrack"
REGISTER_MODEL = False
REGISTERED_MODEL_NAME = "yolo-bytetrack"


def _resolve_source(source: str | Path) -> str:
    """URL이면 OpenCV로 열고, 실패 시 yt-dlp로 다운로드 후 로컬 경로 반환."""
    path_str = str(source)
    if not path_str.startswith(("http://", "https://")):
        return path_str

    cap = cv2.VideoCapture(path_str)
    if cap.isOpened():
        cap.release()
        return path_str

    if not CACHE_VIDEO.exists():
        print("YouTube URL은 OpenCV로 직접 열 수 없어 yt-dlp로 다운로드합니다...", file=sys.stderr)
        ok = subprocess.run(
            ["yt-dlp", "-f", "best[ext=mp4]/best", "-o", str(CACHE_VIDEO), "--newline", path_str],
            timeout=300,
        ).returncode == 0
        if not ok:
            print(
                "오류: yt-dlp로 다운로드 실패. yt-dlp 설치 후 재시도: pip install yt-dlp",
                file=sys.stderr,
            )
            sys.exit(1)
    return str(CACHE_VIDEO)


def main() -> None:
    source = _resolve_source(INPUT_VIDEO)
    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        print(f"오류: 영상을 열 수 없습니다. 경로 확인: {source}", file=sys.stderr)
        sys.exit(1)

    fps = cap.get(cv2.CAP_PROP_FPS)
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    if w <= 0 or h <= 0:
        print("오류: 유효한 프레임 크기를 읽을 수 없습니다.", file=sys.stderr)
        cap.release()
        sys.exit(1)

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    output = cv2.VideoWriter(str(OUTPUT_VIDEO), fourcc, fps, (w, h))
    if not output.isOpened():
        print(f"오류: 출력 파일을 생성할 수 없습니다: {OUTPUT_VIDEO}", file=sys.stderr)
        cap.release()
        sys.exit(1)

    if not os.environ.get("MLFLOW_TRACKING_URI"):
        mlflow.set_tracking_uri(MLRUNS_DIR.as_uri())
    mlflow.set_experiment(EXPERIMENT_NAME)
    with mlflow.start_run(run_name="yolo11n-bytetrack", log_system_metrics=True):
        mlflow.log_params({
            "model": MODEL_WEIGHT,
            "source": str(INPUT_VIDEO)[:200],
            "conf": CONF,
            "tracker": TRACKER,
            "fps": fps,
            "width": w,
            "height": h,
        })

        model = YOLO(MODEL_WEIGHT)
        frame_count = 0
        total_detections = 0
        speed_inference: list[float] = []
        all_confidences: list[float] = []
        detections_per_class: dict[str, int] = {}

        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                results = model.track(
                    frame,
                    tracker=TRACKER,
                    persist=True,
                    conf=CONF,
                )
                annotated = results[0].plot()
                output.write(annotated)

                frame_count += 1
                r = results[0]
                if getattr(r, "speed", None):
                    inf_ms = float(r.speed.get("inference", 0))
                    speed_inference.append(inf_ms)
                    mlflow.log_metric("inference_ms", inf_ms, step=frame_count)
                    if inf_ms > 0:
                        mlflow.log_metric("inference_fps", 1000.0 / inf_ms, step=frame_count)
                boxes = r.boxes
                n_this = len(boxes)
                total_detections += n_this
                mlflow.log_metric("detections_per_frame", n_this, step=frame_count)
                mlflow.log_metric("cumulative_detections", total_detections, step=frame_count)
                for box in boxes:
                    conf_val = box.conf.item()
                    all_confidences.append(conf_val)
                    cls_id = int(box.cls.item())
                    names = getattr(r, "names", {})
                    label = names.get(cls_id, str(cls_id)) if isinstance(names, dict) else (
                        names[cls_id] if 0 <= cls_id < len(names) else str(cls_id)
                    )
                    detections_per_class[label] = detections_per_class.get(label, 0) + 1
                if boxes and hasattr(boxes, "conf"):
                    mean_conf = sum(b.conf.item() for b in boxes) / len(boxes)
                    mlflow.log_metric("confidence_mean_frame", mean_conf, step=frame_count)
        finally:
            cap.release()
            output.release()

        def _avg(x: list[float]) -> float:
            return sum(x) / len(x) if x else 0.0

        summary: dict[str, float] = {
            "frames_processed": float(frame_count),
            "total_detections": float(total_detections),
            "detections_per_frame_avg": total_detections / frame_count if frame_count else 0.0,
        }
        if speed_inference:
            summary["inference_ms_avg"] = _avg(speed_inference)
            summary["inference_fps_avg"] = 1000.0 / _avg(speed_inference) if _avg(speed_inference) > 0 else 0.0
        if all_confidences:
            summary["confidence_mean"] = _avg(all_confidences)
            summary["confidence_max"] = max(all_confidences)
            summary["confidence_min"] = min(all_confidences)
        mlflow.log_metrics(summary)
        for label, count in detections_per_class.items():
            mlflow.log_metric(f"detections/{label}", count)

        if OUTPUT_VIDEO.exists():
            mlflow.log_artifact(str(OUTPUT_VIDEO), "output")
            mlflow.log_param("output_video_path", str(OUTPUT_VIDEO))

        if REGISTER_MODEL:
            try:
                mlflow.pytorch.log_model(
                    model.model,
                    "model",
                    registered_model_name=REGISTERED_MODEL_NAME,
                )
                print(f"✅ 모델 등록: {REGISTERED_MODEL_NAME}")
            except Exception as e:
                print(f"⚠️ Model Registry 등록 실패: {e}")

    print(f"저장 완료: {OUTPUT_VIDEO}")


if __name__ == "__main__":
    main()
