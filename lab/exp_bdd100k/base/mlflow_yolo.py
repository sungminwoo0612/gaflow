"""
MLflow-YOLO 통합 유틸리티
Ultralytics YOLO의 학습 결과를 MLflow에 자동으로 로깅
"""
from pathlib import Path
from typing import Optional, Dict, Any
import mlflow
from ultralytics import YOLO
from ultralytics.utils.callbacks.base import add_integration_callbacks


class MLflowYOLOCallback:
    """YOLO 학습 과정을 MLflow에 자동 로깅하는 콜백"""
    
    def __init__(self, log_model: bool = True, log_plots: bool = True):
        self.log_model = log_model
        self.log_plots = log_plots
        self.run_dir: Optional[Path] = None
    
    def on_pretrain_routine_start(self, trainer):
        """학습 시작 시 실행 디렉토리 저장"""
        self.run_dir = Path(trainer.save_dir)
    
    def on_train_epoch_end(self, trainer):
        """에포크 종료 시 메트릭 로깅"""
        if not mlflow.active_run():
            return
        
        epoch = trainer.epoch
        metrics = {}
        
        # 학습 메트릭
        for key in ["train/box_loss", "train/cls_loss", "train/dfl_loss"]:
            if key in trainer.metrics:
                metrics[key] = trainer.metrics[key]
        
        # Validation 메트릭
        for key in ["metrics/mAP50(B)", "metrics/mAP50-95(B)", 
                    "metrics/precision(B)", "metrics/recall(B)"]:
            if key in trainer.metrics:
                # MLflow 친화적 이름으로 변환
                clean_key = key.replace("metrics/", "val/").replace("(B)", "")
                metrics[clean_key] = trainer.metrics[key]
        
        if metrics:
            mlflow.log_metrics(metrics, step=epoch)
    
    def on_train_end(self, trainer):
        """학습 종료 시 아티팩트 로깅"""
        if not mlflow.active_run() or not self.run_dir:
            return
        
        # Best weights 로깅
        if self.log_model:
            best_pt = self.run_dir / "weights" / "best.pt"
            if best_pt.exists():
                mlflow.log_artifact(str(best_pt), "weights")
            
            last_pt = self.run_dir / "weights" / "last.pt"
            if last_pt.exists():
                mlflow.log_artifact(str(last_pt), "weights")
        
        # 학습 플롯 로깅
        if self.log_plots:
            for plot_name in ["results.png", "confusion_matrix.png", 
                             "F1_curve.png", "PR_curve.png", "P_curve.png", "R_curve.png"]:
                plot_path = self.run_dir / plot_name
                if plot_path.exists():
                    mlflow.log_artifact(str(plot_path), "plots")
    
    def on_val_end(self, validator):
        """Validation 종료 시 메트릭 로깅"""
        if not mlflow.active_run():
            return
        
        # validator.metrics에서 직접 추출 (results_dict 의존성 제거)
        if hasattr(validator, 'metrics') and validator.metrics:
            val_metrics = {
                "val/mAP50": validator.metrics.get("metrics/mAP50(B)", 0),
                "val/mAP50-95": validator.metrics.get("metrics/mAP50-95(B)", 0),
            }
            mlflow.log_metrics(val_metrics)


def train_with_mlflow(
    model_size: str,
    data_yaml: Path,
    epochs: int,
    batch_size: int,
    imgsz: int = 640,
    project_dir: Optional[Path] = None,
    experiment_name: str = "yolo-experiments",
    run_name: Optional[str] = None,
    extra_params: Optional[Dict[str, Any]] = None,
    log_model_registry: bool = False,
    registered_model_name: Optional[str] = None,
) -> YOLO:
    """
    MLflow 통합 YOLO 학습 함수
    
    Args:
        model_size: YOLO 모델 크기 (yolov8n, yolov8s, etc.)
        data_yaml: 데이터셋 YAML 경로
        epochs: 학습 에포크 수
        batch_size: 배치 크기
        imgsz: 입력 이미지 크기
        project_dir: YOLO 실행 결과 저장 디렉토리
        experiment_name: MLflow 실험 이름
        run_name: MLflow 실행 이름
        extra_params: 추가 파라미터 (MLflow에 로깅)
        log_model_registry: 모델 레지스트리 등록 여부
        registered_model_name: 등록할 모델 이름
    
    Returns:
        학습된 YOLO 모델
    """
    mlflow.set_experiment(experiment_name)
    
    run_name = run_name or f"{model_size}-e{epochs}-b{batch_size}"
    
    with mlflow.start_run(run_name=run_name) as run:
        # 파라미터 로깅
        params = {
            "model_size": model_size,
            "epochs": epochs,
            "batch_size": batch_size,
            "imgsz": imgsz,
            "data_yaml": str(data_yaml),
        }
        if extra_params:
            params.update(extra_params)
        mlflow.log_params(params)
        
        # 콜백 설정
        callback = MLflowYOLOCallback()
        model = YOLO(f"{model_size}.pt")
        
        # 콜백 등록
        model.add_callback("on_pretrain_routine_start", callback.on_pretrain_routine_start)
        model.add_callback("on_train_epoch_end", callback.on_train_epoch_end)
        model.add_callback("on_train_end", callback.on_train_end)
        model.add_callback("on_val_end", callback.on_val_end)
        
        # 학습
        if project_dir is None:
            project_dir = Path("mlflow_runs") / experiment_name
        
        results = model.train(
            data=str(data_yaml),
            epochs=epochs,
            batch=batch_size,
            imgsz=imgsz,
            project=str(project_dir),
            name=run.info.run_id,  # MLflow run_id로 동기화
        )
        
        # Final validation
        val_results = model.val()
        
        final_metrics = {
            "final/mAP50": val_results.box.map50,
            "final/mAP50-95": val_results.box.map,
            "final/precision": val_results.box.mp,
            "final/recall": val_results.box.mr,
        }
        mlflow.log_metrics(final_metrics)
        
        # 모델 레지스트리 등록
        if log_model_registry:
            model_name = registered_model_name or f"{experiment_name}-{model_size}"
            mlflow.pytorch.log_model(
                model.model,
                "model",
                registered_model_name=model_name,
            )
        
        return model


def resolve_data_yaml(data_path: str, base_dir: Path) -> Path:
    """
    데이터셋 YAML 경로 자동 탐색
    
    Args:
        data_path: 데이터셋 경로 (상대/절대)
        base_dir: 기준 디렉토리
    
    Returns:
        data.yaml 절대 경로
    """
    p = Path(data_path)
    if not p.is_absolute():
        p = (base_dir / p).resolve()
    
    # 이미 YAML 파일인 경우
    if p.suffix.lower() in (".yaml", ".yml"):
        return p
    
    # 표준 이름 검색
    for name in ("data.yaml", "dataset.yaml", "train.yaml"):
        candidate = p / name
        if candidate.exists():
            return candidate
    
    # 재귀 검색
    for f in p.rglob("*.yaml"):
        if "data" in f.stem.lower() or f.name == "dataset.yaml":
            return f
    
    # 기본값 반환
    return p / "data.yaml"