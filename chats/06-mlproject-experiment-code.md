# Chat 6: MLproject·실험 코드 관리

**날짜**: 30 Jan

---

## 질문

> 실험 코드는 전부 해당 디렉터리 밖에 존재함. 이를 MLproject 단위로 관리가 가능한지?

---

## 핵심 요약

- **MLproject**는 MLflow의 패키징 단위로, **외부 실험 코드**를 독립적인 실행 단위로 관리 가능.
- 각 실험 타입(train/infer/quant)을 별도 MLproject로 두거나, **단일 MLproject에서 entry point로 분기**하는 방식 가능.

---

## 구조 옵션

### Option A: 단일 MLproject + 다중 Entry Points (권장)

- **guardianflow/** (MLOps 코어): MLproject, conda.yaml, scenario/, pipelines/.
- **experiments/** (외부 실험 코드, 별도 repo 가능): yolo_trainer/, mot_benchmark/, quantization/ 등.
- Entry points: train, infer, quant, full_pipeline.
- train/infer/quant는 `--scenario_path`, `--experiment_code_path` 등으로 외부 코드 경로 지정.

### Option B: 실험 타입별 MLproject

- projects/training/, inference/, quantization/ 각각 MLproject + conda.yaml.
- 공통 의존성·시나리오 스키마 공유가 상대적으로 불리.

**권장: Option A** — 공통 의존성 관리 용이, 시나리오 스키마 공유.

---

## MLproject 정의

- **name**: guardianflow.
- **conda_env**: conda.yaml.
- **entry_points**:
  - **train**: scenario_path, experiment_code_path (default: ../experiments/yolo_trainer) → pipelines.train.
  - **infer**: scenario_path, experiment_code_path, source_run_id → pipelines.infer.
  - **quant**: scenario_path, experiment_code_path, source_run_id, backend → pipelines.quant.
  - **full_pipeline**: scenario_path → pipelines.orchestrator.

---

## 파이프라인 구현 (외부 코드 연동)

- **load_external_trainer(code_path)**: sys.path에 code_path 추가, `train.py`에서 Trainer 클래스 동적 로드.
- **load_scenario(scenario_path)**: YAML → TrainingScenario (또는 해당 타입) 변환.
- main: scenario 로드 → Trainer 클래스 로드 → mlflow.start_run → log_params/set_tags → log_artifact(config) → Trainer 인스턴스 생성 시 scenario 주입, **on_epoch_end 콜백 주입** (TrainingMetricsSnapshot → log_metrics) → trainer.train() → best model artifact + register_model.

---

## 외부 실험 코드 인터페이스 규약

- **BaseTrainer**: on_epoch_end, on_batch_end (Runner에서 주입); `train()`, `get_best_model_path()` 추상.
- experiments/yolo_trainer/train.py에서 Trainer 구현: model_config, training_config, dataset_config 받아 YOLO 학습, epoch 종료 시 on_epoch_end(epoch, metrics) 호출.

---

## 실행 방법

```bash
# 단일 학습
mlflow run guardianflow/ -e train -P scenario_path=configs/scenarios/donghwa_welding_v1.yaml -P experiment_code_path=../experiments/yolo_trainer

# 양자화
mlflow run guardianflow/ -e quant -P scenario_path=... -P source_run_id=... -P backend=openvino

# 전체 파이프라인
mlflow run guardianflow/ -e full_pipeline -P scenario_path=...

# 원격 Git repo에서 실행
mlflow run git@github.com:company/guardianflow.git -e train -P scenario_path=...
```

---

## Trade-off

| 방식 | 장점 | 단점 |
|------|------|------|
| MLproject + 외부 코드 경로 | 기존 코드 수정 최소, 유연 | 인터페이스 규약 필요 |
| MLproject 내부에 코드 포함 | 재현성 높음 | 코드 중복, 유지보수 부담 |
| Git submodule | 버전 관리 명확 | submodule 관리 복잡 |

**권장**: MLproject + 외부 코드 경로 + 인터페이스 규약. POC 안정화 후 submodule 검토.
