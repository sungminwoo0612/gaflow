# GuardianFlow × Claude 개발 논의 정리

`질문.txt`에서 Claude와 논의한 **개발 방향성 및 코드**를 주제별 채팅으로 나누어 구조화한 문서입니다.

---

## 채팅 목록 (주제별)

| # | 파일 | 주제 | 핵심 키워드 |
|---|------|------|-------------|
| 1 | [01-mlflow-tracker-logger.md](01-mlflow-tracker-logger.md) | MLflow Tracker vs Logger 분리 | 로깅 구조, experiment.py, callbacks |
| 2 | [02-scenario-container-pipeline.md](02-scenario-container-pipeline.md) | 시나리오 컨테이너·파이프라인 | Scenario 스키마, ScenarioRunner, MLflow 매핑 |
| 3 | [03-experiment-types.md](03-experiment-types.md) | 실험 타입 (학습/추론벤치/양자화) | TrainingScenario, QuantizationScenario, Runner 팩토리 |
| 4 | [04-model-experiment-management.md](04-model-experiment-management.md) | Model/Experiment 관리 전략 | SiteConfig, TaskConfig, Experiment 네이밍 |
| 5 | [05-metrics-detection-mot-system.md](05-metrics-detection-mot-system.md) | YOLO·MOT·시스템 메트릭 | DetectionMetrics, MOTMetrics, SystemMetricsCollector |
| 6 | [06-mlproject-experiment-code.md](06-mlproject-experiment-code.md) | MLproject·실험 코드 관리 | MLproject, entry points, 외부 코드 경로 |
| 7 | [07-experiment-registry-30-dirs.md](07-experiment-registry-30-dirs.md) | 30+ 실험 디렉토리·레지스트리 | experiments.yaml, GenericRunner, 비침습 래퍼 |
| 8 | [08-model-registry.md](08-model-registry.md) | Model Registry 등록·승격·롤백 | candidate/champion/rollback, ModelRegistryManager |
| 9 | [09-experiment-design-sweep-comparison.md](09-experiment-design-sweep-comparison.md) | 실험 설계 (Sweep·Comparison) | SweepRunner, ComparisonRunner, Nested Runs |
| 10 | [10-metrics-store-dashboard-automation.md](10-metrics-store-dashboard-automation.md) | 메트릭 저장·대시보드·자동화 | SeaweedFS, MetricsStore, AutoOptimizer |
| 11 | [11-diagnosis-phase-priority.md](11-diagnosis-phase-priority.md) | 총평·진단 및 Phase 우선순위 | 완성도 평가, Phase 1–4, 권장 우선순위 |
| 12 | [12-phase1-implementation.md](12-phase1-implementation.md) | Phase 1 구현 | Config, TrainingRunner, ModelRegistry, CLI |
| 13 | [13-final-design-workplan.md](13-final-design-workplan.md) | 최종 설계·작업계획 | 컴포넌트 명세, Phase별 작업, 인프라 |
| 14 | [14-phase2-next-steps.md](14-phase2-next-steps.md) | Phase 2·다음 단계 | InferenceRunner, QuantizationRunner, E2E |

---

## 전체 흐름 요약

```
[로깅/실험 구조] → [시나리오·실험 타입] → [메트릭·MLproject·레지스트리]
       → [Model Registry·실험 설계] → [대시보드·자동화]
       → [진단·Phase 1 구현] → [최종 설계·Phase 2]
```

- **설계**: 시나리오 스키마, 실험 타입, 메트릭, MLflow/Experiment/Registry 매핑
- **실행**: Phase 1(최소 동작) → Phase 2(기존 코드·추론·양자화) → Phase 3(스키마 고도화) → Phase 4(대시보드·자동화)

---

## 원본

- 원본 대화: `질문.txt` (Export/노트 기반)
- 날짜: 30 Jan 기준 정리
