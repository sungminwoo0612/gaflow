# Chat 3: 실험 타입 (학습 / 추론벤치 / 양자화)

**날짜**: 30 Jan

---

## 질문

> 실험 타입이 학습, 추론벤치, 양자화 세 가지. 이를 반영한다면?

---

## 핵심 요약

- 실험 타입별로 **공통 기반 스키마 + 타입별 확장**으로 설계.
- 각 타입이 요구하는 파라미터·결과물이 다르므로 **상속/합성** 구조 적용.

---

## 실험 타입별 특성

| 타입 | 입력 | 주요 파라미터 | 결과물 |
|------|------|---------------|--------|
| Training | 데이터셋 | epochs, lr, optimizer | weights, metrics |
| Inference Benchmark | 모델 + 테스트셋 | batch_size, device, precision | latency, throughput, mAP |
| Quantization | 학습된 모델 | quant_method, calibration_size | 경량 모델, 정확도 손실 |

---

## 스키마 설계

- **공통**: DatasetConfig, ModelConfig, EnvironmentConfig.
- **타입별 파라미터**:
  - TrainingParams (epochs, batch_size, lr, optimizer, scheduler, early_stopping)
  - InferenceBenchmarkParams (batch_sizes, warmup_runs, benchmark_runs, input_size)
  - QuantizationParams (method, backend, calibration_size, calibration_method)
- **시나리오**:
  - BaseScenario (name, experiment_type, model, environment, tags, to_flat_params)
  - TrainingScenario, InferenceBenchmarkScenario, QuantizationScenario (각각 타입별 필드 + source_run_id 등).

---

## 타입별 Runner

- **BaseRunner**: 공통 run 시작, log_params, set_tags, _log_scenario_artifact, `_execute()` 추상.
- **TrainingRunner**: 데이터 로드 → 모델 초기화 → 학습 루프(epoch별 log_metrics) → artifact 저장.
- **InferenceBenchmarkRunner**: batch_size별 warmup/benchmark → latency, throughput, detection 메트릭 → artifact.
- **QuantizationRunner**: source_run_id에서 모델 다운로드 → calibration → 양자화 → 정확도 검증 → comparison 메트릭 + artifact.

---

## 팩토리 패턴

```python
def create_runner(scenario: ScenarioType, tracking_uri: str = None) -> BaseRunner:
    runners = {
        "training": TrainingRunner,
        "inference_benchmark": InferenceBenchmarkRunner,
        "quantization": QuantizationRunner,
    }
    return runners[scenario.experiment_type](scenario, tracking_uri)
```

---

## MLflow 실험 구조

```
MLflow Experiments
├── guardianflow-training/
├── guardianflow-quantization/
└── guardianflow-inference_benchmark/
```

각 experiment 내에 Run들이 타입별로 기록됨.
