# Chat 12: Phase 1 구현 (최소 동작 버전)

**날짜**: 30 Jan

---

## 목표

- **단일 학습 → MLflow 기록 → 모델 등록** E2E 동작.

---

## 디렉토리 구조

```
guardianflow/
├── config.py       # 환경 설정
├── runner.py       # 학습 실행기
├── registry.py     # 모델 등록
├── metrics.py      # 메트릭 수집
└── cli.py          # CLI 진입점
```

---

## 구현 요약

### Config (config.py)

- MLFLOW_TRACKING_URI, S3_ENDPOINT_URL (SeaweedFS), AWS_ACCESS_KEY_ID/SECRET, WORK_DIR.
- Config.setup(): 환경변수 설정, WORK_DIR 생성.

### Metrics (metrics.py)

- **TrainingMetrics**: mAP50, mAP50_95, precision, recall, box_loss, cls_loss, dfl_loss → to_dict(prefix).
- **SystemMetrics**: gpu_memory_used_mb, gpu_utilization_pct, inference_time_ms, model_size_mb → to_dict(prefix="sys").
- get_gpu_metrics(device_id): pynvml로 GPU 메트릭.
- get_model_size(model_path): 파일 크기(MB).

### ModelRegistry (registry.py)

- register(run_id, artifact_path, model_name, alias, tags) → ModelInfo.
- promote(model_name, version?) → candidate → champion, 기존 champion → rollback.
- rollback(model_name) → champion ← rollback.
- get_champion_uri(model_name), list_versions(model_name).

### TrainingRunner (runner.py)

- **입력**: experiment_name, model_arch, data_yaml; epochs, batch_size, imgsz, lr, device, tags.
- **내부 로직**: MLflow run 시작 → log_params → YOLO(model_arch).train(data, epochs, batch, ...) → 메트릭 추출(log_metrics) → log_artifact(weights) → ModelRegistry.register(..., @candidate) → Run 종료.
- **출력**: { run_id, status, metrics, model { name, version, alias } }.

### CLI (cli.py)

- `guardianflow train --experiment ... --data ... --model ... --epochs ... --batch ... --customer ... --task ...`
- `guardianflow promote <model_name>`
- `guardianflow list experiments` / `guardianflow list models`
- Python에서 직접: `TrainingRunner(experiment_name, model_arch, data_yaml).run(epochs=..., batch_size=...)`

---

## 검증 체크리스트

```bash
# 1. MLflow 연결 확인
python -c "import mlflow; print(mlflow.get_tracking_uri())"

# 2. YOLO import 확인
python -c "from ultralytics import YOLO; print('OK')"

# 3. 단일 학습 테스트 (짧은 epoch)
guardianflow train --experiment test --data coco128.yaml --epochs 1 --batch 8

# 4. MLflow UI 확인 (http://localhost:5000)

# 5. 모델 등록 확인
guardianflow list models
```

---

## 다음 단계 (Phase 1 완료 후)

- 실제 데이터로 E2E 테스트 (donghwa-entec-ppe 등).
- SeaweedFS 연동 테스트.
- 에러 케이스 보완 (OOM, 학습 실패 등).
- 기존 실험 디렉토리 조사 → Phase 2 설계.
