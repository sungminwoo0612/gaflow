# Chat 14: Phase 2·다음 단계

**날짜**: 30 Jan

---

## Phase 2: 기존 코드 연동 + 추론·양자화

---

## 작업 목록

| ID | 작업 | 우선순위 | 예상 시간 | 의존성 |
|----|------|----------|-----------|--------|
| 2.1 | 기존 실험 디렉토리 실사 | 🔴 높음 | 2h | - |
| 2.2 | InferenceRunner 구현 | 🔴 높음 | 4h | - |
| 2.3 | QuantizationRunner 구현 | 🔴 높음 | 4h | - |
| 2.4 | ExperimentRegistry 구현 | 🟡 중간 | 3h | 2.1 |
| 2.5 | GenericWrapper 구현 | 🟡 중간 | 3h | 2.4 |
| 2.6 | CLI 확장 | 🟢 낮음 | 2h | 2.2–2.5 |
| 2.7 | E2E 테스트 | 🔴 높음 | 2h | 전체 |

---

## 2.1 기존 실험 디렉토리 실사

**먼저 실행할 것:**

```bash
ls -la ~/experiments/
find ~/experiments/donghwa-entec-ppe -type f -name "*.py" | head -20
find ~/experiments -name "*.py" | xargs basename -a | sort | uniq -c | sort -rn | head -20
find ~/experiments -name "*.pt" | head -20
find ~/experiments -name "*.yaml" | head -20
```

결과를 공유하면 **실제 구조에 맞게 코드 조정**.

---

## 2.2 InferenceRunner 구현 요약

- **입력**: experiment_name, model_path, data_yaml; BenchmarkConfig(batch_sizes, warmup_runs, benchmark_runs, conf/iou_threshold, imgsz, device).
- **로직**: mlflow.start_run → set_tag(experiment_type=infer), log_params → YOLO(model_path) 로드 → _run_validation(data_yaml) → detection 메트릭 log_metrics → batch_size별 _run_benchmark (warmup 후 latency 측정) → latency_bs{N}_mean_ms, fps_bs{N}, gpu_memory_bs{N}_mb, best_fps/best_batch_size/best_latency_ms, model_size_mb.
- **출력**: { run_id, status, detection, benchmark[], best }.
- **구현**: guardianflow/inference.py — InferenceRunner.run(config, run_name, tags, source_run_id); _run_validation(model, config); _run_benchmark(model, config, batch_size) → BenchmarkResult(dataclass).

---

## 2.3 QuantizationRunner 구현 요약

- **입력**: experiment_name, source_run_id, data_yaml(optional); QuantConfig(backend, precision, imgsz, calibration_data, calibration_size).
- **로직**: mlflow.start_run → set_tag(experiment_type=quant, source_run_id, quant_backend, quant_precision) → _download_source_model() (mlflow.artifacts.download_artifacts) → original_size_mb log_metric → YOLO(original_path) 로드 → _benchmark_model(original) → _export_model(model, config) (model.export(format=backend, half/int8, data=calibration)) → quantized_size_mb → _benchmark_model(quantized) → comparison (accuracy_drop_mAP50, speedup_ratio, compression_ratio) log_metrics → log_artifact(quantized_path, "weights") → register(model_name={base}__{backend}_{precision}, @candidate).
- **출력**: { run_id, status, original, quantized, comparison, model }.
- **구현**: guardianflow/quantization.py — QuantizationRunner.run(config, run_name, tags, register); _download_source_model, _export_model, _benchmark_model, _get_model_name.

---

## 다음 단계

- 2.1 실사 결과 반영 후 ExperimentRegistry YAML 스키마·GenericWrapper 동작 방식 확정.
- 2.2, 2.3 완료 후 CLI infer/quant 명령 연결 및 E2E 테스트.
