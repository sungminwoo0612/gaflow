# Chat 8: Model Registry 등록·승격·롤백

**날짜**: 30 Jan

---

## 질문

> 학습, 양자화 수행 이후 모델이 MLflow Model Registry에 등록되는 로직이 현재 있는지?

---

## 현재 상태 분석

- 시나리오 → 모델명 생성: ✅ (BaseScenario.get_registered_model_name()).
- Alias 전략 정의: ✅ (문서: candidate/champion/rollback).
- **실제 등록 코드**: ❌ Runner에 미구현.
- **Alias 관리 코드**: ❌ 미구현.

---

## Model Registry 등록 로직 추가

### ModelRegistryManager (scenario/model_registry.py)

- **ModelAlias**: CANDIDATE, CHAMPION, ROLLBACK.
- **register_model(run_id, artifact_path, model_name, alias=CANDIDATE, tags)**:
  - `runs:/{run_id}/{artifact_path}` 로 등록.
  - mlflow.register_model 후 set_model_version_tag, set_registered_model_alias.
  - 반환: RegisteredModelInfo (name, version, run_id, aliases).
- **promote_to_champion(model_name, version=None)**:
  - version 없으면 현재 candidate 버전 사용.
  - 현재 champion → rollback alias로 이동.
  - candidate → champion alias로 설정.
- **rollback(model_name)**: rollback alias 버전을 champion으로, 기존 champion은 candidate로.
- **get_champion(model_name)**, **get_model_uri(model_name, alias)**, **list_versions(model_name)**.
- **_get_version_by_alias(model_name, alias)** 내부 헬퍼.

---

## Runner에 등록 로직 통합

- **TrainingRunner._execute()** 마지막:
  - best weights artifact 저장.
  - `model_name = scenario.get_registered_model_name()`.
  - `registry.register_model(run_id, "weights/best.pt", model_name, ModelAlias.CANDIDATE, tags)`.
- **QuantizationRunner._execute()** 마지막:
  - 양자화 모델명 = `get_registered_model_name(variant)` (예: .../ppe__openvino_int8).
  - register_model(..., alias=CANDIDATE, tags에 backend, precision, source_run_id 등).

---

## CLI

- `guardianflow promote <model_name>` → promote_to_champion.
- `guardianflow rollback <model_name>` → rollback.
- `guardianflow models` → 목록/버전 조회.

---

## 사용 예시

```bash
# 학습 → 자동 @candidate 등록
python -m guardianflow.cli run donghwa-entec-ppe --type train --version v3

# 검증 후 승격
python -m guardianflow.cli promote "donghwa-entec/busan-plant1/welding/ppe"

# 문제 시 롤백
python -m guardianflow.cli rollback "donghwa-entec/busan-plant1/welding/ppe"

# 양자화 → 별도 모델로 등록 (ppe__openvino_int8 @candidate)
python -m guardianflow.cli run donghwa-entec-ppe --type quant --version v3
```

---

## Model Registry 구조 (최종)

- FP32: `{customer}/{region}-{plant}/{zone}/{task}` (예: donghwa-entec/busan-plant1/welding/ppe).
- 양자화: `{base}__{backend}_{precision}` (예: .../ppe__openvino_int8).
- 버전별 alias: @candidate, @champion, @rollback.
