# GAFlow

## 환경 셋업 (Conda + 의존성)

Conda 환경 생성부터 의존성 일괄 설치까지 한 번에 수행합니다.  
**사전 요구:** [Miniconda](https://docs.conda.io/en/latest/miniconda.html) 또는 Anaconda 설치 후 `conda`가 PATH에 있어야 합니다.

```powershell
# Windows (PowerShell) - 프로젝트 루트에서
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\scripts\setup_env.ps1
```

```bash
# Linux / macOS (Bash)
bash scripts/setup_env.sh
```

**옵션**

| 옵션 | 설명 |
|------|------|
| `--dry-run` | 실제 실행 없이 수행할 명령만 출력 |
| `--verbose` | 상세 로그 출력 |
| `--recreate` | 기존 환경 삭제 후 새로 생성 |

예: `.\scripts\setup_env.ps1 -Verbose -Recreate` / `bash scripts/setup_env.sh --verbose --recreate`

셋업 후 활성화: `conda activate gaflow`

---

## 데이터셋
1. 사람 + 안전조끼(산업안전/CCTV 근접) 
  YOLO HighVis and Person Detection Dataset:
  https://www.kaggle.com/datasets/tudorhirtopanu/yolo-highvis-and-person-detection-dataset


2. 차량 여러 종류 (승용차, 트럭, 버스, 오토바이 등)
  Vehicle Detection 8 Classes
  https://datasetninja.com/vehicle-detection-8-classes


3. bdd100k
  bdd100k
  https://www.kaggle.com/datasets/solesensei/solesensei_bdd100k
  - 사람 + 차량 + 오토바이
  - YOLO 학습용으로 바로 쓰기 좋음
  - 일부만 받아도 수 GB 수준으로 컷 가능

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\scripts\download_datasets.ps1
```

## MLflow 실험 관리

MLflow를 사용하여 YOLO 모델 학습 실험을 추적하고 관리합니다.

### 구조

```
gaflow/
├── MLproject              # MLflow 프로젝트 정의
├── conda.yaml            # Conda 환경 설정
└── mlflow_experiments/   # 실험 스크립트
    ├── exp_baseline.py      # 실험 1: 기본 파라미터
    ├── exp_hyperparams.py   # 실험 2: 하이퍼파라미터 튜닝
    ├── exp_model_size.py    # 실험 3: 모델 크기 비교
    ├── run_experiments.ps1  # Windows 실행 스크립트
    └── run_experiments.sh   # Linux/Mac 실행 스크립트
```

### 실험 실행

#### 개별 실험 실행

```powershell
# 실험 1: 기본 파라미터
mlflow run . -e experiment_baseline -P epochs=5 -P batch_size=16 -P model_size=yolov8n

# 실험 2: 하이퍼파라미터 튜닝
mlflow run . -e experiment_hyperparams -P epochs=10 -P batch_size=32 -P learning_rate=0.01 -P model_size=yolov8s

# 실험 3: 모델 크기 비교
mlflow run . -e experiment_model_size -P epochs=5 -P batch_size=16 -P model_size=yolov8m
```

#### 모든 실험 일괄 실행

```powershell
# Windows
.\mlflow_experiments\run_experiments.ps1

# Linux/Mac
bash mlflow_experiments/run_experiments.sh
```

### 실험 결과 확인

```powershell
# MLflow UI 실행
mlflow ui

# 브라우저에서 확인
# http://localhost:5000
```

### 실험 시나리오

1. **기본 파라미터 실험** (`experiment_baseline`)
   - 기본 설정으로 모델 학습
   - 파라미터: epochs, batch_size, model_size

2. **하이퍼파라미터 튜닝** (`experiment_hyperparams`)
   - 학습률, 배치 크기 등 하이퍼파라미터 조정
   - 파라미터: epochs, batch_size, learning_rate, model_size

3. **모델 크기 비교** (`experiment_model_size`)
   - 다양한 모델 크기(nano, small, medium, large) 성능 비교
   - 파라미터: epochs, batch_size, model_size

### 추적되는 메트릭

- 학습 손실: `train/box_loss`, `train/cls_loss`, `train/dfl_loss`
- 검증 메트릭: `val/mAP50`, `val/mAP50-95`, `val/precision`, `val/recall`
- 하이퍼파라미터: 모든 학습 파라미터
- 모델 아티팩트: 학습된 모델 파일