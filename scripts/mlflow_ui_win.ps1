# MLflow Tracking Server (Windows): workers=1 로 실행하여 WinError 10022 방지
# 참고: https://github.com/encode/uvicorn/issues/514
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot\..
mlflow server --host 127.0.0.1 --port 5000 --workers 1 @args
