# Chat 10: 메트릭 저장·대시보드·자동화

**날짜**: 30 Jan

---

## 질문

> 수집된 메트릭 지표가 로컬 SeaweedFS에 저장되고, 대시보드 지표에 따라 고도화하는 법

---

## 핵심 구조

- **실험 실행 → MLflow → SeaweedFS(저장) → 대시보드(시각화) → 인사이트 → 고도화.**

---

## 아키텍처

- **GuardianFlow**: Experiments(Runner) → MLflow Server(Tracking) → SeaweedFS(Artifact Store).
- MLflow: PostgreSQL(metadata), S3 호환(SeaweedFS) artifacts.
- **Dashboard Layer**: Grafana / Streamlit / Custom React — 실험 비교, 모델 성능 트렌드, 시스템 리소스, 알람·자동화 트리거.

---

## 1. SeaweedFS + MLflow 연동

- **docker-compose**: seaweedfs-master(9333), seaweedfs-volume(8080), seaweedfs-filer(8888, S3 8333); postgres(5432); mlflow(5000) — backend-store-uri=postgres, artifacts-destination=s3://mlflow-artifacts/.
- **config/mlflow_config.py**: MLFLOW_TRACKING_URI, MLFLOW_S3_ENDPOINT_URL, AWS_ACCESS_KEY_ID/SECRET(SeaweedFS는 빈 값 허용).
- 환경변수로 boto3/mlflow가 SeaweedFS S3 엔드포인트 사용하도록 설정.

---

## 2. 메트릭 저장 확장 (MetricsStore)

- **목적**: MLflow 외 별도 저장소로 **대시보드 쿼리 최적화**.
- **MetricRecord**: timestamp, run_id, experiment_name, run_name; customer, site, zone, task; experiment_type, experiment_design, model_architecture, model_version; detection(mAP50, mAP50_95, precision, recall); mot(mota, idf1, hota); system(inference_time_ms, fps, gpu_*); comparison(accuracy_drop, speedup_ratio, compression_ratio).
- **MetricsStore**: save_metrics(record) → MLflow는 이미 Runner에서 저장, **로컬 JSON Lines** (metrics_YYYY-MM-DD.jsonl) append; export_to_parquet(start_date, end_date) → Parquet로 집계 (Grafana/BI 연동).
- Runner 완료 시 MetricsStore.save_metrics() 호출해 이중 저장 (선택).

---

## 3. Dashboard API (FastAPI)

- `/api/metrics/summary` (customer, days): 고객별 요약.
- `/api/metrics/trend` (customer, task, metric): 시계열 트렌드.
- `/api/metrics/comparison`: 모델 비교.
- `/api/metrics/alerts`: 성능 알림 목록.
- MetricsStore 또는 MLflow Client로 조회.

---

## 4. 자동화 (AutoOptimizer)

- **Triggers**: 조건 → 액션.
  - mAP50 < 0.75 → HP Sweep / 재학습.
  - Latency > 30ms → 양자화(INT8).
  - GPU util < 50% → 배치 크기 증가 등.
- **automation/optimizer.py**: 트리거 조건 평가 → 해당 액션(새 실험 생성, MLflow run 등) 실행.
- cron 또는 Airflow에서 주기적 실행: metrics 조회 → alerts 확인 → 자동 고도화 실행.
- **CLI**: metrics summary/trend, alerts list, optimize check/run, metrics export (parquet).

---

## 대시보드 지표 → 고도화 흐름 (요약)

- Dashboard에서 메트릭 모니터링 → 트리거 발동 → HP Sweep / Quantize / Batch 조정 등 → New Experiment → MLflow Run → Model Registry 반영.

---

## 구성요소 요약

| 구성요소 | 기술 스택 | 역할 |
|----------|-----------|------|
| 저장 | SeaweedFS (S3) + PostgreSQL | Artifacts + Metadata |
| 추적 | MLflow | 실험 관리 |
| 쿼리 | MetricsStore (JSON/Parquet) | 대시보드용 최적화 |
| 시각화 | Grafana / FastAPI | 대시보드 |
| 자동화 | AutoOptimizer + Triggers | 고도화 파이프라인 |
