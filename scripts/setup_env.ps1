# =============================================================================
# GAFlow Conda 환경 생성 및 의존성 일괄 셋업 (Windows PowerShell)
# - conda 환경 생성/갱신, pip 의존성 설치, 환경 검증
# =============================================================================

param(
    [switch]$DryRun,
    [switch]$Verbose,
    [switch]$Recreate
)

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
$ErrorActionPreference = "Stop"

# --- 경로: 스크립트 기준 프로젝트 루트 ---
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$CondaYaml = Join-Path $ProjectRoot "conda.yaml"

# --- Conda 사용 가능 여부 확인 ---
function Test-Conda {
    try {
        $null = Get-Command conda -ErrorAction Stop
        if ($Verbose) { Write-Host "[VERBOSE] conda found." -ForegroundColor Gray }
        return $true
    } catch {
        Write-Host "[ERROR] conda not found. Install Miniconda/Anaconda and add to PATH." -ForegroundColor Red
        return $false
    }
}

# --- conda.yaml 존재 확인 ---
function Test-CondaYaml {
    if (-not (Test-Path $CondaYaml)) {
        Write-Host "[ERROR] conda.yaml not found: $CondaYaml" -ForegroundColor Red
        return $false
    }
    if ($Verbose) { Write-Host "[VERBOSE] conda.yaml: $CondaYaml" -ForegroundColor Gray }
    return $true
}

# --- 환경 이름 추출 (conda.yaml 첫 줄 name: xxx) ---
function Get-EnvName {
    $line = Get-Content $CondaYaml -First 1
    if ($line -match "^\s*name:\s*(.+)$") { return $Matches[1].Trim() }
    return "gaflow"
}

# --- 환경 생성 (최초 또는 --Recreate 시) ---
function New-GaflowEnv {
    $envName = Get-EnvName
    if ($DryRun) {
        Write-Host "[DRY-RUN] conda env create -f `"$CondaYaml`"" -ForegroundColor Yellow
        return $true
    }
    Write-Host "[CREATE] Creating conda env: $envName from conda.yaml" -ForegroundColor Cyan
    Push-Location $ProjectRoot
    try {
        conda env create -f $CondaYaml
        if ($LASTEXITCODE -ne 0) { return $false }
        return $true
    } finally {
        Pop-Location
    }
}

# --- 환경 갱신 (이미 있을 때) ---
function Update-GaflowEnv {
    $envName = Get-EnvName
    if ($DryRun) {
        Write-Host "[DRY-RUN] conda env update -f `"$CondaYaml`" --prune" -ForegroundColor Yellow
        return $true
    }
    Write-Host "[UPDATE] Updating conda env: $envName from conda.yaml" -ForegroundColor Cyan
    Push-Location $ProjectRoot
    try {
        conda env update -f $CondaYaml --prune
        if ($LASTEXITCODE -ne 0) { return $false }
        return $true
    } finally {
        Pop-Location
    }
}

# --- 환경 제거 후 재생성 ---
function Remove-GaflowEnv {
    $envName = Get-EnvName
    if ($DryRun) {
        Write-Host "[DRY-RUN] conda env remove -n $envName -y" -ForegroundColor Yellow
        return $true
    }
    Write-Host "[REMOVE] Removing env: $envName" -ForegroundColor Yellow
    conda env remove -n $envName -y
    $LASTEXITCODE -eq 0
}

# --- 환경 존재 여부 ---
function Test-GaflowEnvExists {
    $envName = Get-EnvName
    $list = conda env list --json 2>$null | ConvertFrom-Json
    $found = $list.envs | Where-Object { $_ -match [regex]::Escape($envName) }
    return ($null -ne $found -and $found.Count -gt 0)
}

# --- 환경 검증 (activate 후 python/import 확인) ---
function Test-GaflowEnv {
    $envName = Get-EnvName
    if ($DryRun) {
        Write-Host "[DRY-RUN] Would run: conda run -n $envName python -c \"import mlflow; import ultralytics\"" -ForegroundColor Yellow
        return $true
    }
    Write-Host "[VERIFY] Checking imports in env: $envName" -ForegroundColor Cyan
    $code = "import mlflow; import ultralytics; print('OK')"
    $out = conda run -n $envName python -c $code 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Verification failed: $out" -ForegroundColor Red
        return $false
    }
    Write-Host "  $out" -ForegroundColor Green
    return $true
}

# --- 메인 ---
function Main {
    Write-Host "============================================" -ForegroundColor Cyan
    Write-Host " GAFlow environment setup" -ForegroundColor Cyan
    Write-Host "============================================" -ForegroundColor Cyan

    if (-not (Test-Conda)) { exit 1 }
    if (-not (Test-CondaYaml)) { exit 1 }

    $exists = Test-GaflowEnvExists
    if ($Recreate -and $exists) {
        if (-not (Remove-GaflowEnv)) { exit 1 }
        $exists = $false
    }

    if (-not $exists) {
        if (-not (New-GaflowEnv)) { exit 1 }
    } else {
        if (-not (Update-GaflowEnv)) { exit 1 }
    }

    if (-not (Test-GaflowEnv)) { exit 1 }

    $envName = Get-EnvName
    Write-Host ""
    Write-Host "============================================" -ForegroundColor Green
    Write-Host " Setup complete." -ForegroundColor Green
    Write-Host " Activate: conda activate $envName" -ForegroundColor White
    Write-Host "============================================" -ForegroundColor Green
}

Main
