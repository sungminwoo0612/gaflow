#!/bin/bash
# MLflow 실험 실행 스크립트

echo "=========================================="
echo "MLflow 실험 실행 시작"
echo "=========================================="

# 실험 1: 기본 파라미터
echo ""
echo "[1/3] 기본 파라미터 실험 실행 중..."
mlflow run . -e experiment_baseline \
    -P epochs=5 \
    -P batch_size=16 \
    -P model_size=yolov8n

# 실험 2: 하이퍼파라미터 튜닝
echo ""
echo "[2/3] 하이퍼파라미터 튜닝 실험 실행 중..."
mlflow run . -e experiment_hyperparams \
    -P epochs=10 \
    -P batch_size=32 \
    -P learning_rate=0.01 \
    -P model_size=yolov8s

# 실험 3: 모델 크기 비교
echo ""
echo "[3/3] 모델 크기 비교 실험 실행 중..."
mlflow run . -e experiment_model_size \
    -P epochs=5 \
    -P batch_size=16 \
    -P model_size=yolov8m

echo ""
echo "=========================================="
echo "모든 실험 완료!"
echo "=========================================="
echo ""
echo "MLflow UI 실행:"
echo "  mlflow ui"
echo ""
echo "실험 결과 확인:"
echo "  http://localhost:5000"
