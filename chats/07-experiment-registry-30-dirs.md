# Chat 7: 30+ 실험 디렉토리·레지스트리

**날짜**: 30 Jan

---

## 질문

> ~/experiments/ 아래 donghwa-entec-ppe, donghwa-entec-fall, sampyo-gimhae-bct 식으로 30개 넘는 디렉터리가 있고, 각각 아래에 학습, 추론, 양자화 등이 섞여 있음. 이를 어떻게 관리할지?

---

## 핵심 분석

- **현재**: 고객/태스크별 디렉토리에 실험 코드가 비정형으로 혼재.
- **전략**: 기존 구조 유지 + **메타데이터 레이어** 추가 (비침습적 래퍼 + 레지스트리).

---

## 현재 구조 추정

```
~/experiments/
├── donghwa-entec-ppe/
│   ├── train_yolov11_v1.py, train_yolov11_v2.py
│   ├── infer_benchmark.py, export_openvino.py
│   ├── weights/, data/
├── donghwa-entec-fall/
├── sampyo-gimhae-bct/
└── ... (30+ 디렉토리)
```

**문제**: 파일명/구조 비일관, 실험 타입 구분 어려움, 메타데이터 부재, 재현성 확보 어려움.

---

## 전략: 비침습적 래퍼 + 레지스트리

- **guardianflow/**: MLproject, scenario/, pipelines/, **registry/experiments.yaml**.
- **~/experiments/**: 기존 코드 **수정 없이** 유지.
- **experiments.yaml**: 실험 디렉토리별 메타데이터 (path, site, task, entry_points).

---

## 레지스트리 YAML 구조

```yaml
# guardianflow/registry/experiments.yaml
experiments:
  donghwa-entec-ppe:
    path: ~/experiments/donghwa-entec-ppe
    site:
      customer: donghwa-entec
      region: busan
      plant: plant1
      zone: welding
    task:
      type: ppe
      classes: [headgear, harness, hook]
    entry_points:
      train:
        default: train_yolov11_v2.py
        patterns: ["train*.py"]
        args_template: "--epochs {epochs} --batch {batch_size}"
      infer:
        default: infer_benchmark.py
      quant:
        default: export_openvino.py
```

---

## GenericRunner (래퍼)

- 레지스트리에서 실험명으로 path, entry_points 조회.
- `run(experiment_dir_name, type, version, script_override, extra_params)`:
  - MLflow experiment = site 기반 네이밍.
  - start_run → set_tags(script, wrapped) → **subprocess**로 해당 디렉토리에서 스크립트 실행 (기본 스크립트 또는 지정 스크립트).
  - stdout/stderr artifact, 실행 후 생성/수정된 *.pt, *.csv, *.png 등 자동 수집.
- 기존 스크립트는 **그대로** 실행되며, MLflow만 외부에서 감쌈.

---

## CLI

- `guardianflow run donghwa-entec-ppe --type train --version v3`
- `guardianflow run donghwa-entec-ppe --type train --script train_yolov11_custom.py`
- `guardianflow scan` → 기존 디렉토리 스캔하여 레지스트리 초안 생성.
- `guardianflow list` → 등록된 실험 목록.

---

## 점진적 마이그레이션

| 단계 | 작업 | 기존 코드 영향 |
|------|------|----------------|
| 1. 스캔 | cli scan으로 레지스트리 초안 | 없음 |
| 2. 메타데이터 | experiments.yaml 수동 보완 | 없음 |
| 3. 래핑 실행 | cli run으로 MLflow 기록 시작 | 없음 |
| 4. 인터페이스 표준화 | 점진적으로 BaseTrainer 상속 | 최소 수정 |
| 5. 통합 | 검증된 실험만 GuardianFlow 코어로 이동 | 선택적 |

**핵심**: 30개+ 디렉토리를 한 번에 수정하지 않고, **외부에서 메타데이터만 추가**해 MLflow 추적부터 시작.
