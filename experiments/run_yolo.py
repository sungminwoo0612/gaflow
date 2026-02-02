import os
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

from contextlib import nullcontext
from pathlib import Path
from typing import Iterator

import cv2
import mlflow
import torch
from ultralytics import YOLO

# System metrics: True면 GPU/CPU/메모리 수집 후 MLflow "System metrics"에 step별·요약 로깅
LOG_SYSTEM_METRICS = True
SYSTEM_METRICS_EVERY_N_FRAMES = 10  # N프레임마다 샘플 (오버헤드 완화)

OUTPUT_VIDEO = Path("experiments") / "yolo_output.mp4"
FPS = 30.0
MAX_FRAMES = 300  # OOM 방지: 처리할 최대 프레임 (약 10초)
SKIP_FRAMES = 2   # N장마다 1장만 처리 (메모리·시간 절약)
IMGSZ = 640       # 추론 해상도 (작을수록 VRAM 절약)
CONF = 0.5
MODEL_WEIGHT = "yolo11n.pt"
VIDEO_SOURCE = "https://www.youtube.com/watch?v=Fb1e6ytEniA"
# RTX 5080/5090 (Blackwell sm_120): PyTorch 나이틀리 cu128 필요
# pip install --pre torch torchvision torchaudio --index-url https://download.pytorch.org/whl/nightly/cu128

# MOT 평가: True면 model.track() + MOT 포맷 출력. 로컬 영상 권장 (URL은 OpenCV에서 실패할 수 있음).
USE_TRACKING = False
MOT_PREDICTIONS_PATH = Path("experiments") / "mot_predictions.txt"
# Ground truth (MOT 포맷) 경로 지정 시 motmetrics로 MOTA/IDF1 등 계산 후 MLflow 로깅. 예: MOT_GT_PATH=./gt/gt.txt
MOT_GT_PATH = os.environ.get("MOT_GT_PATH", "")

DEVICE: int | str = 0 if torch.cuda.is_available() else "cpu"
print(f"🔍 Using device: {DEVICE}")

EXPERIMENT_NAME = "yolo-video-inference"
# Model Registry: True면 Run 종료 시 모델을 "Models"에 등록 (yolo-video-inference)
REGISTER_MODEL = True
REGISTERED_MODEL_NAME = "yolo-video-inference"
# Traces: True면 MLflow Traces 탭에 load_model / inference_loop / write_output / mot_evaluation span 기록
ENABLE_TRACES = True


def _start_span(name: str):
    """MLflow Traces span. mlflow.start_span (2.15+) 또는 mlflow.tracing.start_span."""
    if not ENABLE_TRACES:
        return nullcontext()
    try:
        return mlflow.start_span(name=name)
    except AttributeError:
        try:
            from mlflow.tracing import start_span as _tracing_start_span
            return _tracing_start_span(name=name)
        except Exception:
            return nullcontext()


def _iter_frames_and_results(
    model: YOLO,
    source: str,
    max_frames: int,
    skip_frames: int,
    conf: float,
    imgsz: int,
    device: int | str,
    use_tracking: bool,
) -> Iterator[tuple[object, object]]:
    """프레임과 YOLO 결과를 스트리밍. use_tracking이면 track(persist=True), 아니면 predict(stream=True)."""
    if use_tracking:
        cap = cv2.VideoCapture(source)
        if not cap.isOpened():
            print("⚠️ 트래킹 모드: 영상 열기 실패(로컬 파일 경로 권장). detection 모드로 진행.")
            use_tracking = False
        else:
            frame_idx = 0
            while frame_idx < max_frames:
                ret, frame = cap.read()
                if not ret:
                    break
                if frame_idx % skip_frames == 0:
                    result = model.track(
                        frame,
                        persist=True,
                        conf=conf,
                        save=False,
                        show=False,
                        imgsz=imgsz,
                        device=device,
                    )
                    if result and len(result) > 0:
                        result[0].orig_img = frame
                        yield frame, result[0]
                frame_idx += 1
            cap.release()
            return
    if not use_tracking:
        results = model.predict(
            source=source,
            stream=True,
            conf=conf,
            save=False,
            show=False,
            imgsz=imgsz,
            device=device,
        )
        count = 0
        for idx, result in enumerate(results):
            if count >= max_frames:
                break
            if idx % skip_frames != 0:
                continue
            count += 1
            yield result.orig_img.copy(), result


def _get_system_metrics(device_id: int = 0) -> dict[str, float]:
    """GPU(pynvml)·프로세스(psutil) 메트릭 수집. sys/* 키로 반환."""
    out: dict[str, float] = {}
    try:
        import psutil
        p = psutil.Process()
        out["sys/cpu_percent"] = p.cpu_percent() or 0.0
        out["sys/memory_rss_mb"] = p.memory_info().rss / (1024 * 1024)
        out["sys/memory_vms_mb"] = p.memory_info().vms / (1024 * 1024)
    except Exception:
        pass
    if not torch.cuda.is_available():
        return out
    try:
        import pynvml
        try:
            pynvml.nvmlInit()
        except Exception:
            pass  # 이미 초기화됨
        handle = pynvml.nvmlDeviceGetHandleByIndex(device_id)
        mem = pynvml.nvmlDeviceGetMemoryInfo(handle)
        util = pynvml.nvmlDeviceGetUtilizationRates(handle)
        out["sys/gpu_memory_used_mb"] = mem.used / (1024 * 1024)
        out["sys/gpu_memory_total_mb"] = mem.total / (1024 * 1024)
        out["sys/gpu_utilization_pct"] = float(util.gpu)
        try:
            out["sys/gpu_temperature_c"] = float(pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU))
        except Exception:
            pass
        try:
            out["sys/gpu_power_w"] = pynvml.nvmlDeviceGetPowerUsage(handle) / 1000.0  # mW → W
        except Exception:
            pass
    except Exception:
        pass
    return out


def _write_mot_line(f: object, frame_id: int, track_id: int, x1: float, y1: float, w: float, h: float, conf: float) -> None:
    """MOT Challenge 포맷: frame,id,x,y,w,h,conf,-1,-1,-1. motmetrics load 시 (1,1) 보정하므로 x,y는 1-based."""
    f.write(f"{frame_id},{track_id},{x1+1:.2f},{y1+1:.2f},{w:.2f},{h:.2f},{conf:.4f},-1,-1,-1\n")


mlflow.set_experiment(EXPERIMENT_NAME)

# log_system_metrics=True → MLflow 내장 수집기가 system/* 메트릭을 "System metrics" 탭에 표시
with mlflow.start_run(run_name="yolo11n-youtube-inference", log_system_metrics=True):
    mlflow.log_params({
        "model": MODEL_WEIGHT,
        "source": VIDEO_SOURCE,
        "conf": CONF,
        "imgsz": IMGSZ,
        "max_frames": MAX_FRAMES,
        "skip_frames": SKIP_FRAMES,
        "fps": FPS,
        "device": str(DEVICE),
        "use_tracking": USE_TRACKING,
    })

    print("🚀 데이터셋 준비 중...")
    _span = _start_span("load_model")
    with _span:
        model = YOLO(MODEL_WEIGHT)
        results_iter = _iter_frames_and_results(
            model, VIDEO_SOURCE, MAX_FRAMES, SKIP_FRAMES, CONF, IMGSZ, DEVICE, USE_TRACKING
        )
    print(f"🎥 영상 추론 시작: {VIDEO_SOURCE} (최대 {MAX_FRAMES} frames, {SKIP_FRAMES}장마다 1장)")

    writer: cv2.VideoWriter | None = None
    frame_count = 0
    total_detections = 0
    detections_per_class: dict[str, int] = {}
    all_confidences: list[float] = []
    speed_preprocess: list[float] = []
    speed_inference: list[float] = []
    speed_postprocess: list[float] = []
    mot_file = None
    if USE_TRACKING:
        MOT_PREDICTIONS_PATH.parent.mkdir(parents=True, exist_ok=True)
        mot_file = open(MOT_PREDICTIONS_PATH, "w")

    # System metrics 수집 (step별 + 요약용)
    sys_samples: list[dict[str, float]] = [] if LOG_SYSTEM_METRICS else []

    _inference_span = _start_span("inference_loop")
    with _inference_span:
        for frame, result in results_iter:
            if frame_count >= MAX_FRAMES:
                break
            frame_count += 1
            if hasattr(frame, "shape"):
                h, w = frame.shape[:2]
            else:
                h, w = result.orig_img.shape[:2]
                frame = result.orig_img.copy()
            if writer is None:
                OUTPUT_VIDEO.parent.mkdir(parents=True, exist_ok=True)
                fourcc = cv2.VideoWriter_fourcc(*"mp4v")
                writer = cv2.VideoWriter(str(OUTPUT_VIDEO), fourcc, FPS, (w, h))

            # YOLO speed (ms): preprocess, inference, postprocess — step별 로깅으로 라인 차트
            if getattr(result, "speed", None):
                sp = result.speed
                pre_ms = float(sp.get("preprocess", 0))
                inf_ms = float(sp.get("inference", 0))
                post_ms = float(sp.get("postprocess", 0))
                speed_preprocess.append(pre_ms)
                speed_inference.append(inf_ms)
                speed_postprocess.append(post_ms)
                inference_ms_this = inf_ms
                mlflow.log_metric("inference_ms", inf_ms, step=frame_count)
                mlflow.log_metric("inference_preprocess_ms", pre_ms, step=frame_count)
                mlflow.log_metric("inference_postprocess_ms", post_ms, step=frame_count)
                if inf_ms > 0:
                    mlflow.log_metric("inference_fps", 1000.0 / inf_ms, step=frame_count)

            boxes = result.boxes
            detections_this_frame = 0
            confidences_this_frame: list[float] = []
            for box in boxes:
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                conf_val = box.conf.item()
                cls = box.cls.item()
                label = result.names[int(cls)]
                total_detections += 1
                detections_this_frame += 1
                all_confidences.append(conf_val)
                confidences_this_frame.append(conf_val)
                detections_per_class[label] = detections_per_class.get(label, 0) + 1
                if mot_file is not None:
                    track_id = int(box.id) if getattr(box, "id", None) is not None else 0
                    _write_mot_line(mot_file, frame_count, track_id, x1, y1, x2 - x1, y2 - y1, conf_val)
                print(f"🔍 검출: {label} (Conf: {conf_val:.2f})")
                cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
                cv2.putText(frame, label, (int(x1), int(y1) - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

            # step별 메트릭 → MLflow에서 라인 차트로 표시
            mlflow.log_metric("detections_per_frame", detections_this_frame, step=frame_count)
            mlflow.log_metric("cumulative_detections", total_detections, step=frame_count)
            if confidences_this_frame:
                mean_conf = sum(confidences_this_frame) / len(confidences_this_frame)
                mlflow.log_metric("confidence_mean_frame", mean_conf, step=frame_count)
            # 프레임당 누적 평균 추론 시간 (추이 확인용)
            if speed_inference:
                running_avg_ms = sum(speed_inference) / len(speed_inference)
                mlflow.log_metric("inference_forward_ms_running_avg", running_avg_ms, step=frame_count)

            # System metrics: N프레임마다 샘플 → MLflow System metrics 탭에 라인 차트
            if LOG_SYSTEM_METRICS and frame_count % SYSTEM_METRICS_EVERY_N_FRAMES == 0:
                sm = _get_system_metrics(device_id=int(DEVICE) if isinstance(DEVICE, int) else 0)
                if sm:
                    sys_samples.append(sm)
                    mlflow.log_metrics(sm, step=frame_count)

            writer.write(frame)

    _write_span = _start_span("write_output")
    with _write_span:
        if mot_file is not None:
            mot_file.close()
            print(f"✅ MOT 예측 저장: {MOT_PREDICTIONS_PATH}")
        if writer is not None:
            writer.release()
            print(f"✅ 저장 완료: {OUTPUT_VIDEO} ({frame_count} frames)")

    # YOLO 결과 지표 요약
    def _avg(x: list[float]) -> float:
        return sum(x) / len(x) if x else 0.0

    summary: dict[str, float] = {
        "frames_processed": float(frame_count),
        "total_detections": float(total_detections),
        "detections_per_frame": total_detections / frame_count if frame_count else 0.0,
    }
    if speed_inference:
        summary["inference_preprocess_ms"] = _avg(speed_preprocess)
        summary["inference_forward_ms"] = _avg(speed_inference)
        summary["inference_postprocess_ms"] = _avg(speed_postprocess)
        summary["inference_fps"] = 1000.0 / _avg(speed_inference) if _avg(speed_inference) > 0 else 0.0
    if all_confidences:
        summary["confidence_mean"] = _avg(all_confidences)
        summary["confidence_max"] = max(all_confidences)
        summary["confidence_min"] = min(all_confidences)

    mlflow.log_metrics(summary)
    for label, count in detections_per_class.items():
        mlflow.log_metric(f"detections/{label}", count)

    # System metrics 요약 (max/mean) → MLflow
    if sys_samples:
        keys = list(sys_samples[0].keys())
        for k in keys:
            vals = [s[k] for s in sys_samples if k in s and s[k] is not None]
            if vals:
                mlflow.log_metric(f"{k}_max", max(vals))
                mlflow.log_metric(f"{k}_mean", sum(vals) / len(vals))
        print(f"✅ System metrics 로깅: {len(sys_samples)} 샘플, {keys}")

    if OUTPUT_VIDEO.exists():
        mlflow.log_artifact(str(OUTPUT_VIDEO), "output")
        mlflow.log_param("output_video_path", str(OUTPUT_VIDEO))

    # MOT 평가: Ground truth가 있고 예측 MOT 파일이 있으면 motmetrics로 MOTA/IDF1 등 계산 후 MLflow 로깅
    gt_path = Path(MOT_GT_PATH).resolve() if MOT_GT_PATH else None
    _mot_span = _start_span("mot_evaluation")
    with _mot_span:
        if gt_path and gt_path.exists() and MOT_PREDICTIONS_PATH.exists():
            try:
                import motmetrics as mm

                gt_df = mm.io.loadtxt(str(gt_path), fmt="mot15-2D", min_confidence=1)
                pred_df = mm.io.loadtxt(str(MOT_PREDICTIONS_PATH), fmt="mot15-2D")
                acc = mm.utils.compare_to_groundtruth(gt_df, pred_df, "iou", distth=0.5)
                mh = mm.metrics.create()
                summary = mh.compute(acc, metrics=mm.metrics.motchallenge_metrics, name="yolo")
                mot_metrics = {f"mot/{k}": float(v) for k, v in summary.items() if k != "name"}
                mlflow.log_metrics(mot_metrics)
                mlflow.log_param("mot_gt_path", str(gt_path))
                print(f"✅ MOT 메트릭 로깅: {list(mot_metrics.keys())}")
            except Exception as e:
                print(f"⚠️ motmetrics 평가 실패: {e}")

        if MOT_PREDICTIONS_PATH.exists():
            mlflow.log_artifact(str(MOT_PREDICTIONS_PATH), "mot")

    # .pt 파일을 아티팩트로 로깅 (로컬에 있을 때) → Artifacts/weights/ 에 저장
    _pt_path = Path(MODEL_WEIGHT).resolve() if Path(MODEL_WEIGHT).exists() else Path.cwd() / MODEL_WEIGHT
    if _pt_path.exists():
        mlflow.log_artifact(str(_pt_path), "weights")
        mlflow.log_param("weights_artifact", _pt_path.name)

    # Model Registry: Run의 모델을 "Models"에 등록 → MLflow UI Models 탭에서 버전·스테이징 관리
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