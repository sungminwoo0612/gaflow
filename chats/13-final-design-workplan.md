# Chat 13: 최종 설계·작업계획

**날짜**: 30 Jan

---

## 질문

> 최종 설계안의 핵심 컴포넌트와 로직들을 구체적으로 정리. 이를 통해 작업계획을 상세히 만들 예정.

---

## 1. 핵심 컴포넌트 구조

```
guardianflow/
├── core/                    # 핵심 로직
│   ├── config.py
│   ├── runner.py
│   ├── registry.py
│   └── metrics.py
├── scenario/                # Phase 3
│   ├── schema.py
│   ├── experiment_design.py
│   └── factory.py
├── adapters/                # 외부 연동
│   ├── generic_wrapper.py
│   └── experiment_registry.py
├── dashboard/               # Phase 4
│   ├── api.py
│   ├── metrics_store.py
│   └── automation.py
└── cli.py
```

---

## 2. 컴포넌트별 상세 명세 (요약)

| 컴포넌트 | 입력/출력 요약 | 구현 상태 |
|----------|----------------|-----------|
| Config | MLFLOW_TRACKING_URI, S3, WORK_DIR, EXPERIMENTS_BASE | ✅ Phase 1 |
| TrainingRunner | experiment_name, model_arch, data_yaml, epochs, batch… → run_id, metrics, model | ✅ Phase 1 |
| InferenceRunner | experiment_name, model_path, data_yaml, batch_sizes… → run_id, detection/mot/system metrics | ❌ Phase 2 |
| QuantizationRunner | experiment_name, source_run_id, backend, precision… → run_id, original/quantized/comparison | ❌ Phase 2 |
| ModelRegistry | register, promote, rollback, get_champion_uri, list_versions | ✅ Phase 1 |
| Metrics | Detection/MOT/System 정의, get_gpu_metrics, get_model_size | ✅ 정의·부분 구현 |
| GenericWrapper | experiment_name, script_path, working_dir, args, artifact_patterns | ❌ Phase 2 |
| ExperimentRegistry | experiments.yaml, get/list/find/scan_and_generate | ❌ Phase 2 |
| Scenario Schema | BaseScenario, Training/Inference/QuantizationScenario, Site/Task/Model/Env/Dataset | ✅ 설계, Phase 3 코드화 |
| Experiment Design | SINGLE/SWEEP/COMPARISON, SweepConfig, ComparisonConfig | ✅ 설계, Phase 3 |
| MetricsStore | MetricRecord, save_metrics, query_metrics, export_to_parquet | ❌ Phase 4 |
| Dashboard API | /api/metrics/summary, trend, comparison, alerts | ❌ Phase 4 |
| AutoOptimizer | 트리거(mAP50<0.75, latency>30ms, util<50%) → 액션(재학습, 양자화, 배치 증가) | ❌ Phase 4 |

---

## 3. 인프라 구성

- **Docker Compose**: MLflow(:5000), PostgreSQL(:5432), SeaweedFS(Master 9333, Volume 8080, Filer 8888, S3 8333), Grafana(:3000), Dashboard API(:8000).
- MLflow: backend-store-uri=postgres, artifacts-destination=s3:// (SeaweedFS).

---

## 4. CLI 명령어 (Phase별)

| 명령어 | 설명 | Phase |
|--------|------|-------|
| guardianflow train | 학습 실행 | 1 |
| guardianflow promote | 모델 승격 | 1 |
| guardianflow list | 목록 조회 | 1 |
| guardianflow infer | 추론 벤치마크 | 2 |
| guardianflow quant | 양자화 | 2 |
| guardianflow wrap | 기존 코드 래핑 | 2 |
| guardianflow scan | 디렉토리 스캔 | 2 |
| guardianflow sweep | HP 탐색 | 3 |
| guardianflow compare | 모델 비교 | 3 |
| guardianflow metrics / alerts / optimize | 메트릭·알림·자동 고도화 | 4 |

---

## 5. Phase별 작업 범위

- **Phase 1 (완료)**: Config, TrainingRunner, ModelRegistry, Metrics 정의, CLI (train, promote, list).
- **Phase 2**: InferenceRunner, QuantizationRunner, GenericWrapper, ExperimentRegistry, CLI 확장 (infer, quant, wrap, scan).
- **Phase 3**: Scenario Schema 코드화, SweepRunner, ComparisonRunner, Factory, CLI (sweep, compare).
- **Phase 4**: MetricsStore, Dashboard API, Grafana, AutoOptimizer, CLI (metrics, alerts, optimize).

---

## 6. 데이터 흐름 요약

- [실험 코드] → [Runner] → log_params / log_metrics / log_artifact / register_model → [MLflow Server] → PostgreSQL(metadata), SeaweedFS(artifacts).
- Model Registry: @candidate → promote → @champion (기존 champion → @rollback); rollback 시 champion ← rollback.
- 배포/서빙은 champion URI 참조.
