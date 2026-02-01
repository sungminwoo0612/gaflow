# Chat 9: 실험 설계 (Sweep·Comparison)

**날짜**: 30 Jan

---

## 질문

> 실험별 케이스를 더 고려해본다면? 단독모델, 2개 이상 비교, 단일 모델 여러 파라미터 수정, 비양자화 vs 양자화 등. 실험별 케이스를 어떻게 쪼갤 수 있는지, 쪼개야 하는지.

---

## 실험 케이스 분류 체계

- **실험 타입**: train / infer / quant (기존 3가지).
- **실험 설계/목적**에 따른 분류 추가: 단일 실행, 스윕, 비교 등.

---

## 실험 케이스 매트릭스

| 실험 목적 | 모델 수 | 변수 | 예시 | MLflow 구조 |
|-----------|---------|------|------|-------------|
| Baseline | 1 | 없음 | 최초 학습 | Single Run |
| Hyperparameter Sweep | 1 | N개 파라미터 조합 | lr, batch_size 그리드 | Parent + Child Runs |
| Architecture Comparison | N | 아키텍처 | yolov11n vs s vs m | Parallel Runs |
| Ablation Study | 1 | 구성요소 on/off | augmentation 효과 | Parent + Child Runs |
| A/B Benchmark | 2 | 없음 | v2 vs v3 성능 비교 | Comparison Run |
| Quantization Comparison | 1 | backend/precision | fp32 vs int8 vs fp16 | Parent + Child Runs |
| Cross-site Generalization | 1 | 테스트 데이터셋 | A사이트 모델 → B사이트 | Multi-dataset Run |

---

## 실험 설계 타입 정의 (experiment_design.py)

- **ExperimentDesign**: SINGLE, SWEEP, COMPARISON, ABLATION, QUANTIZATION_COMPARE.
- **SweepConfig**: parameters (dict[str, list]), strategy (grid/random/bayesian), max_runs → generate_combinations().
- **ComparisonConfig**: models, run_ids, model_versions, quantization_variants, datasets.
- **AblationConfig**: baseline, components (제거/변경할 구성요소).

---

## 시나리오 확장

- BaseScenario에 design, sweep_config, comparison_config, ablation_config 추가.
- TrainingScenario.with_sweep(params, strategy), InferenceBenchmarkScenario.with_comparison(...), QuantizationScenario.with_quant_comparison(variants) 등 빌더 메서드.

---

## SweepRunner

- 시나리오의 sweep_config에서 조합 생성.
- Parent run 시작 → 각 조합마다 nested child run, 파라미터 오버라이드한 시나리오로 BaseRunner 실행.
- 순차 또는 ThreadPoolExecutor로 병렬 실행.
- Parent run에 best.run_id, best.params, best.mAP50 등 로깅.

---

## ComparisonRunner

- comparison_config에 따라: 아키텍처 비교, run_ids 비교, 양자화 variant 비교, 데이터셋 비교.
- 각각 nested child run으로 벤치마크/메트릭 수집 후 parent run에 비교 요약 로깅.

---

## MLflow 구조 (Nested Runs)

- Sweep: 1 Parent + N Child (sweep.index, sweep.strategy 태그).
- Comparison: 1 Parent + N Child (comparison.variable, comparison.value 태그).
- 양자화 비교: Parent + Child (quant-openvino_int8 등).

---

## 결론 정리

| 분류 기준 | 분리 여부 | 이유 |
|-----------|-----------|------|
| 실험 타입 (train/infer/quant) | ✅ 분리 | 입출력·파이프라인 다름 |
| 실험 설계 (single/sweep/comparison) | ✅ 분리 | 실행 방식·MLflow 구조 다름 |
| 파라미터 변형 | ❌ 통합 | Sweep 내 Child Run |
| 모델/양자화 변형 | ❌ 통합 | Comparison 내 Child Run |

**핵심**: 실험 타입 × 실험 설계 조합은 많지만, Runner 상속/조합으로 처리. 과도한 분리는 복잡도만 증가.
