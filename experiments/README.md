# experiments

YOLO 영상 추론·트래킹·MOT 평가 실험.

## run_yolo.py

- **Detection**: 기본 `model.predict(stream=True)` — URL/로컬 영상 지원.
- **Tracking**: `USE_TRACKING = True` 시 `model.track(persist=True)` 사용, MOT 포맷 예측 파일 출력.  
  - 로컬 영상 경로 권장(URL은 OpenCV에서 실패할 수 있음).

### MOT 평가 (motmetrics)

1. **트래킹 + MOT 예측 파일**  
   `USE_TRACKING = True`, `VIDEO_SOURCE`를 로컬 영상으로 두고 실행 → `experiments/mot_predictions.txt` 생성.

2. **Ground truth**  
   MOT Challenge 포맷(GT)을 준비.  
   - 한 줄: `frame,id,x,y,w,h,conf,-1,-1,-1` (1-based frame/id, 픽셀 좌표).

3. **motmetrics 실행**  
   GT 경로를 지정한 뒤 같은 실험을 다시 실행하면 motmetrics로 MOTA/IDF1 등 계산 후 MLflow에 로깅:

   ```bash
   set MOT_GT_PATH=C:\path\to\gt.txt
   python experiments/run_yolo.py
   ```

   또는 터미널에서:

   ```bash
   export MOT_GT_PATH=/path/to/gt.txt
   python experiments/run_yolo.py
   ```

4. **MLflow에 로깅되는 MOT 메트릭**  
   `mot/mota`, `mot/idf1`, `mot/idp`, `mot/idr`, `mot/recall`, `mot/precision`, `mot/num_switches` 등.

### TrackEval

동일 MOT 포맷 예측/GT를 사용해 [TrackEval](https://github.com/JonathonLuiten/TrackEval)로도 평가 가능.  
디렉터리 구조는 [MOT Challenge](https://motchallenge.net/) 규격을 따르면 됨.

```bash
pip install trackeval
# TrackEval 레포의 스크립트/설정으로 GT·예측 경로 지정 후 실행
```

예측 파일은 `run_yolo.py`에서 `USE_TRACKING = True`로 생성한 `mot_predictions.txt`를 시퀀스별로 배치하면 됨.

### Models (Model Registry)

- **REGISTER_MODEL = True** (기본값)이면 Run 종료 시 사용한 YOLO 모델을 MLflow **Models** 탭에 등록합니다.
- 등록 이름: **REGISTERED_MODEL_NAME** (`yolo-video-inference`).
- MLflow UI **Models**에서 버전·스테이징(Staging/Production)·별칭 관리 가능.
- 끄려면 `REGISTER_MODEL = False`.

**yolo11n.pt만 Models에 올리기** (추론 없이 모델 업로드만):

```bash
python experiments/upload_yolo_to_mlflow.py
python experiments/upload_yolo_to_mlflow.py --model path/to/yolo11n.pt --registered-name yolo-video-inference
```

- `--model`: .pt 경로 또는 이름 (기본: `yolo11n.pt`, 없으면 Ultralytics가 자동 다운로드).
- Run에 `weights/<파일명>` 아티팩트 + PyTorch 모델이 등록됨.

### Traces

- **ENABLE_TRACES = True** (기본값)이면 Run 동안 다음 span이 **Traces** 탭에 기록됩니다.
  - `load_model`: 모델 로드 + 이터레이터 생성
  - `inference_loop`: 프레임별 추론 루프 전체
  - `write_output`: MOT 파일·영상 저장
  - `mot_evaluation`: motmetrics 평가(GT 있을 때)
- MLflow UI **Traces**에서 구간별 소요 시간·계층 구조 확인 가능.
- 끄려면 `ENABLE_TRACES = False`. MLflow 2.15+ 권장.
