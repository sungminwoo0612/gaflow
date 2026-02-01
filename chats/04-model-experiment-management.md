# Chat 4: Model / Experiment 관리 전략

**날짜**: 30 Jan

---

## 질문

> Model, Experiment 관리 전략을 기존 컨벤션과 맞추고 싶음.

---

## 핵심 분석

- **Experiment** = 현장/고객사/구역 (site context).
- **Run** = 실험 타입(train/infer/quant) + 버전.
- **Registered Model** = 태스크별 모델 + 양자화 variant.
- 이 구조와 시나리오 스키마를 **정합**시키는 것이 목표.

---

## 통합 스키마 설계

### 현장 컨텍스트 (Experiment 레벨)

- **SiteConfig**: customer, region, plant, zone.
  - `to_experiment_name()` → `{customer}/{region}-{plant}/{zone}`.
  - `to_tags()` → site.* 태그.

### 태스크 정의

- **TaskConfig**: type (ppe, fall, fire, collision, stuck), classes.
  - `to_tags()` → task.* 태그.

### 공통 컴포넌트

- **DatasetConfig**: version, dvc_hash, path, image_count → data.* 태그.
- **ModelConfig**: architecture, input_size, weights_path, num_classes → to_params().
- **EnvironmentConfig**: device, precision, seed.

### 실험 타입별 파라미터

- TrainingParams, InferenceBenchmarkParams, QuantizationParams (기존과 동일).

### 시나리오 (Base + 타입별)

- **BaseScenario**: name, version, experiment_type, site, task, model, environment, dataset.
  - `get_experiment_name()` → site.to_experiment_name().
  - `get_run_name()` → `{task}-{architecture}-{exp_type}-{version}`.
  - `get_registered_model_name(variant)` → `{site}/{task}` 또는 `{site}/{task}__{variant}`.
  - `to_all_tags()`, `to_all_params()`.
- TrainingScenario, InferenceBenchmarkScenario, QuantizationScenario에서 타입별 params/tags 확장.

---

## 사용 예시 (동화엔텍 시나리오)

- 학습: SiteConfig(donghwa-entec, busan, plant1, welding) → experiment `donghwa-entec/busan-plant1/welding`, run_name `ppe-yolov11l-train-v2`, registered model `donghwa-entec/busan-plant1/welding/ppe`.
- 양자화: 동일 site/task, get_registered_model_name() → `.../ppe__openvino_int8`.

---

## MLflow 구조 매핑 (최종)

- **Experiments**: 현장 컨텍스트별 (customer/region-plant/zone).
- **Runs**: 실험 타입별 (train/infer/quant) run들.
- **Registered Models**: site/zone/task, 양자화는 `task__backend_precision` 형태.

---

## 디렉토리 구조

- scenario/schema.py (위 dataclass 전체), runner.py, factory.py.
- pipelines/train.py, benchmark.py, quantize.py.
- experiments/ 하위에 고객·사이트별 디렉토리 (donghwa_entec/, sampyo/ 등).
- configs/sites/ (optional) YAML로 사이트 정보 관리.
