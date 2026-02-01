# Chat 1: MLflow Tracker vs Logger 분리

**날짜**: 30 Jan

---

## 질문

> Mlflow로 로직을 짜는데 tracker와 logger를 나눠야 할까? 이렇게 세 가지 로깅(Metrics/Parameters/Artifacts)을 따로 파일화?

---

## 핵심 요약

- **MLflow에서 Metrics/Parameters/Artifacts 로깅을 별도 파일로 분리할 필요 없음.**
- 단일 `mlflow` 모듈이 세 가지를 **통합 관리**하도록 설계하는 것이 적절함.

---

## 권장 구조

**분리 기준: 기능별이 아닌 책임별**

```
ml_tracking/
├── experiment.py    # MLflow run 컨텍스트 관리
├── callbacks.py    # 훈련 프레임워크 콜백 (PyTorch Lightning, YOLO 등)
└── config.py       # tracking URI, experiment name 설정
```

**분리하지 않는 이유**

- `mlflow.log_metric()`, `log_param()`, `log_artifact()`는 모두 **동일한 run context** 안에서 호출되어야 함.
- 세 로깅 타입을 분리하면 run context 공유를 위한 불필요한 의존성이 생김.
- MLflow는 이미 내부적으로 분리 저장함 (metrics → time-series DB, artifacts → object storage).

---

## 최소 구현 예시

```python
# experiment.py
import mlflow
from contextlib import contextmanager

@contextmanager
def tracked_run(experiment_name: str, run_name: str = None):
    mlflow.set_experiment(experiment_name)
    with mlflow.start_run(run_name=run_name) as run:
        yield run

def log_training_step(metrics: dict, params: dict = None, artifacts: list[str] = None):
    """단일 함수에서 세 타입 모두 처리 - run context 내에서 호출"""
    if params:
        mlflow.log_params(params)
    mlflow.log_metrics(metrics)
    if artifacts:
        for path in artifacts:
            mlflow.log_artifact(path)
```

**사용 예**

```python
with tracked_run("guardianflow-ppe-detection", run_name="yolo-v8-exp-001"):
    mlflow.log_params({"lr": 0.001, "batch_size": 16, "epochs": 100})
    for epoch in range(100):
        mlflow.log_metrics({"loss": loss, "mAP50": map50}, step=epoch)
    mlflow.log_artifact("weights/best.pt")
```

---

## Tracker vs Logger 분리가 의미 있는 경우

| 상황 | 분리 여부 | 이유 |
|------|----------|------|
| 단일 프레임워크 (YOLO, Lightning) | ❌ | 프레임워크 콜백이 이미 통합 처리 |
| 멀티 백엔드 (MLflow + W&B + 자체 DB) | ✅ | 추상화 레이어 필요 |
| 분산 훈련 (multi-node) | ✅ | rank 0만 로깅하는 로직 분리 |

**GuardianFlow POC 단계에서는 분리 불필요. 복잡도만 증가.**
