# MLflow 실험 실행 스크립트 (PowerShell)

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "MLflow 실험 실행 시작" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# 실험 1: 기본 파라미터
Write-Host ""
Write-Host "[1/3] 기본 파라미터 실험 실행 중..." -ForegroundColor Green
mlflow run . -e experiment_baseline `
    -P epochs=5 `
    -P batch_size=16 `
    -P model_size=yolov8n

# 실험 2: 하이퍼파라미터 튜닝
Write-Host ""
Write-Host "[2/3] 하이퍼파라미터 튜닝 실험 실행 중..." -ForegroundColor Green
mlflow run . -e experiment_hyperparams `
    -P epochs=10 `
    -P batch_size=32 `
    -P learning_rate=0.01 `
    -P model_size=yolov8s

# 실험 3: 모델 크기 비교
Write-Host ""
Write-Host "[3/3] 모델 크기 비교 실험 실행 중..." -ForegroundColor Green
mlflow run . -e experiment_model_size `
    -P epochs=5 `
    -P batch_size=16 `
    -P model_size=yolov8m

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "모든 실험 완료!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "MLflow UI 실행:" -ForegroundColor Yellow
Write-Host "  mlflow ui" -ForegroundColor White
Write-Host ""
Write-Host "실험 결과 확인:" -ForegroundColor Yellow
Write-Host "  http://localhost:5000" -ForegroundColor White
