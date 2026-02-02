# lab – 데이터셋별 YOLO 실험 (MLProject 예시)

`test.py`로 다운로드한 데이터셋별로 간단한 YOLO 학습 실험을 MLProject로 실행하는 예시입니다.

## 디렉터리 구조

| 디렉터리 | 데이터셋 (Kaggle slug) |
|----------|-------------------------|
| `exp_highvis_person/` | tudorhirtopanu/yolo-highvis-and-person-detection-dataset |
| `exp_bdd100k/` | solesensei/solesensei_bdd100k |
| `exp_vehicle_8class/` | sakshamjn/vehicle-detection-8-classes-object-detection |

각 디렉터리에는 `MLproject`, `train.py`가 있으며, conda 환경은 프로젝트 루트의 `conda.yaml`을 참조합니다.

## 사전 준비

1. 데이터셋 다운로드 (프로젝트 루트에서):

   ```bash
   python test.py
   # 또는
   python scripts/download_datasets.py
   ```

2. 다운로드 후 `datasets/<owner>/<dataset_name>/` 아래에 실제 경로가 생깁니다.  
   필요하면 `mlflow run` 시 `-P data_path=...` 로 경로를 지정하세요.

## 실행 (MLflow)

프로젝트 루트(`gaflow`)에서:

```bash
# BDD100k 실험 (기본 파라미터)
mlflow run lab/exp_bdd100k

# Vehicle 8-class, epochs·batch 변경
mlflow run lab/exp_vehicle_8class -P epochs=3 -P batch_size=8

# High-Vis Person, 데이터 경로 지정
mlflow run lab/exp_highvis_person -P data_path=datasets/tudorhirtopanu/yolo-highvis-and-person-detection-dataset/1
```

## MLproject 파라미터 (공통)

- `data_path`: 데이터셋 루트 또는 data.yaml 경로 (기본값은 위 표의 slug 기준)
- `epochs`: 학습 에폭 (기본 5)
- `batch_size`: 배치 크기 (기본 16)
- `model_size`: YOLO 모델 크기 (기본 yolov8n)
