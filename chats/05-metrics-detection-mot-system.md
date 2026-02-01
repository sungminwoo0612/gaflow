# Chat 5: YOLO 기본·MOT·시스템 메트릭

**날짜**: 30 Jan

---

## 질문

> Yolo 기본 및 MOT 메트릭을 기록해야 함. 시스템 메트릭도 기록해야 함.

---

## 핵심 요약

- 메트릭을 **3개 카테고리**로 분리: Detection Metrics, MOT Metrics, System Metrics.
- 실험 타입별로 기록 대상·시점이 다름.

---

## 메트릭 카테고리별 정의

| 카테고리 | 실험 타입 | 기록 시점 |
|----------|-----------|-----------|
| Detection (YOLO) | train, infer | epoch별 / 최종 |
| MOT (Tracking) | infer | 최종 |
| System | train, infer, quant | step별 / 최종 |

---

## 스키마 확장

### DetectionMetrics (YOLO)

- mAP50, mAP50_95, precision, recall, f1; box_loss, cls_loss, dfl_loss; per_class_ap.
- `to_mlflow_dict(prefix="det")`.

### MOTMetrics (CLEAR MOT + HOTA)

- mota, motp, idf1; id_switches, id_precision, id_recall; frag, mt, ml, pt; hota, deta, assa, loca; gt_tracks, pred_tracks, fp, fn.
- `to_mlflow_dict(prefix="mot")`.

### SystemMetrics

- inference_time_ms, p50/p95/p99; fps, throughput; gpu_memory_used_mb, gpu_utilization_pct, gpu_power_watts, gpu_temperature_c; cpu_utilization_pct, cpu_memory_used_mb; model_size_mb, model_params_m, model_flops_g.
- `to_mlflow_dict(prefix="sys")`.

### 실험 타입별 메트릭 컨테이너

- **TrainingMetricsSnapshot**: epoch, detection, system → epoch별 log_metrics(step=epoch).
- **InferenceMetricsResult**: detection, mot, system → 최종 log_metrics.
- **QuantizationMetricsResult**: original/quantized detection·system + comparison (accuracy_drop, speedup_ratio, compression_ratio) → det.original, sys.original, det.quantized, sys.quantized, comparison.*.

---

## 메트릭 수집 유틸리티

- **SystemMetricsCollector**: pynvml로 GPU 메트릭, `measure_latency()` 컨텍스트로 추론 시간, `get_latency_stats()`, `to_system_metrics()`.
- **get_model_stats(model, input_size)**: thop으로 params, FLOPs.

---

## Runner 통합

- TrainingRunner: epoch마다 TrainingMetricsSnapshot → log_metrics(step=epoch); 모델 통계 params.
- InferenceBenchmarkRunner: validation → detection; benchmark 루프 → system; tracking 사용 시 MOT 계산 → InferenceMetricsResult.
- QuantizationRunner: 원본/양자화 벤치마크 각각 → QuantizationMetricsResult.

---

## MLflow 메트릭 구조 (최종)

- **det.***: mAP50, mAP50_95, precision, recall, loss들, ap.{class_name}.
- **mot.***: mota, motp, idf1, hota, id_switches, frag, mt, ml, pt 등.
- **sys.***: inference_time_ms, fps, gpu_*, model_params_m, model_flops_g 등.
- **comparison.*** (quant만): accuracy_drop_mAP50, speedup_ratio, compression_ratio.

| 메트릭 | train | infer | quant |
|--------|-------|-------|-------|
| det.mAP50 | ✅ (step) | ✅ | ✅ (orig/quant) |
| det.loss | ✅ (step) | - | - |
| mot.* | - | ✅ | - |
| sys.inference_time | - | ✅ | ✅ |
| sys.gpu_* | ✅ | ✅ | ✅ |
| comparison.* | - | - | ✅ |
