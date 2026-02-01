# Chat 2: 시나리오 컨테이너·파이프라인

**날짜**: 30 Jan

---

## 질문

> 시나리오 = 어떤 데이터셋 + 어떤 데이터 처리 + 어떤 모델 + 어떤 모델 처리 + 어떤 실험 설정 + 실험 과정 + 실험 결과  
> 시나리오라는 컨테이너 단위를 만들어서 이를 파이프라인으로 운용하고 싶음

---

## 핵심 요약

- **시나리오** = 실험의 재현 가능한 전체 명세.
- MLflow 구조(Experiment → Run)와 매핑하되, 시나리오를 **선언적 config + 실행 파이프라인**으로 분리하는 것이 핵심.

---

## 개념 매핑

| 시나리오 컴포넌트 | MLflow 매핑 | 저장 방식 |
|-------------------|-------------|-----------|
| 데이터셋 정의 | Run Tag / Param | dataset_id, version |
| 데이터 처리 | Param + Artifact | transform config, DVC ref |
| 모델 정의 | Param | model_name, architecture |
| 모델 처리 (학습 설정) | Param | optimizer, scheduler |
| 실험 설정 | Param | seed, device, epochs |
| 실험 과정 | Metrics (step) | loss, mAP per epoch |
| 실험 결과 | Metrics + Artifacts | final metrics, weights |

---

## 시나리오 스키마 설계

- `DatasetConfig`, `PreprocessConfig`, `ModelConfig`, `TrainingConfig` dataclass 정의.
- **Scenario** = name + dataset + preprocess + model + training + tags.
- `Scenario.to_flat_params()` → MLflow `log_params`용 flat dict.

---

## 파이프라인 실행 구조

- **ScenarioRunner**: 시나리오 → MLflow Run 실행기.
  - `run()`: experiment 설정 → start_run → log_params/set_tags → _log_scenario_artifact → _prepare_data → _build_model → _train → _save_results → return run_id.
- 시나리오 config 자체를 YAML artifact로 저장해 재현성 확보.

---

## 디렉토리 구조

```
guardianflow/
├── scenario/
│   ├── schema.py      # Scenario, DatasetConfig 등 dataclass
│   ├── runner.py       # ScenarioRunner
│   └── registry.py    # (optional) 시나리오 버전 관리
├── pipelines/
│   ├── data.py
│   ├── train.py
│   └── evaluate.py
├── experiments/
│   ├── ppe_baseline.py
│   └── emergency_detection.py
└── configs/scenarios/   # YAML 시나리오
```

---

## Trade-off 정리

| 접근 방식 | 장점 | 단점 |
|-----------|------|------|
| Python dataclass | 타입 체크, IDE 지원, 코드 재사용 | 비개발자 접근 어려움 |
| YAML config | 선언적, 버전 관리 용이 | 스키마 검증 별도 필요 |
| Hydra | 계층적 config 오버라이드 | 러닝 커브, 디버깅 복잡 |

**POC 단계 권장**: dataclass로 시작 → 시나리오가 많아지면 YAML + Pydantic 전환.
