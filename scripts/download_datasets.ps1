# =============================================================================
# 데이터셋 다운로드 스크립트 (Windows PowerShell)
# 대상: BDD100K (이미지 + 라벨) + UA-DETRAC (이미지 + 어노테이션)
# 총 예상 용량: ~10GB
# =============================================================================

# UTF-8 인코딩 설정
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

$ErrorActionPreference = "Stop"

# --- 설정 ---
$BASE_DIR = "$env:USERPROFILE\datasets"
$BDD_DIR  = "$BASE_DIR\bdd100k"
$DETRAC_DIR = "$BASE_DIR\ua-detrac"

# 디렉토리 생성
New-Item -ItemType Directory -Force -Path $BDD_DIR | Out-Null
New-Item -ItemType Directory -Force -Path $DETRAC_DIR | Out-Null

# --- 다운로드 함수 (재시도 로직 포함) ---
function Download-FileWithRetry {
    param(
        [string]$Url,
        [string]$Destination,
        [int]$MaxRetries = 3,
        [int]$RetryDelay = 5
    )
    
    $retryCount = 0
    while ($retryCount -lt $MaxRetries) {
        try {
            Write-Host "    Attempt $($retryCount + 1)/$MaxRetries..." -ForegroundColor Gray
            Invoke-WebRequest -Uri $Url -OutFile $Destination -UseBasicParsing -ErrorAction Stop
            return $true
        }
        catch {
            $retryCount++
            if ($retryCount -ge $MaxRetries) {
                Write-Host "  [ERROR] Failed to download after $MaxRetries attempts" -ForegroundColor Red
                Write-Host "    Error: $($_.Exception.Message)" -ForegroundColor Red
                return $false
            }
            Write-Host "    Retrying in $RetryDelay seconds..." -ForegroundColor Yellow
            Start-Sleep -Seconds $RetryDelay
        }
    }
    return $false
}

Write-Host "============================================" -ForegroundColor Cyan
Write-Host " [1/2] BDD100K Download" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan

# BDD100K - ETH Zurich 미러 (인증 불필요)
$bddFiles = @(
    @{ url = "https://dl.cv.ethz.ch/bdd100k/data/100k_images_train.zip";             size = "3.7GB" },
    @{ url = "https://dl.cv.ethz.ch/bdd100k/data/100k_images_val.zip";               size = "542MB" },
    @{ url = "https://dl.cv.ethz.ch/bdd100k/data/bdd100k_det_20_labels_trainval.zip"; size = "53MB"  }
)

foreach ($f in $bddFiles) {
    $filename = Split-Path $f.url -Leaf
    $dest = "$BDD_DIR\$filename"
    if (Test-Path $dest) {
        Write-Host "  [SKIP] $filename (already exists)" -ForegroundColor Yellow
    } else {
        Write-Host "  [DOWN] $filename ($($f.size))..." -ForegroundColor Green
        if (Download-FileWithRetry -Url $f.url -Destination $dest) {
            Write-Host "  [DONE] $filename" -ForegroundColor Green
        } else {
            Write-Host "  [FAIL] $filename - Please check your network connection" -ForegroundColor Red
            Write-Host "    URL: $($f.url)" -ForegroundColor Gray
        }
    }
}

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host " [2/2] UA-DETRAC Download" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan

# UA-DETRAC - 공식 직접 링크
$detracFiles = @(
    @{ url = "https://detrac-db.rit.albany.edu/Data/DETRAC-train-data.zip";  size = "~3.5GB" },
    @{ url = "https://detrac-db.rit.albany.edu/Data/DETRAC-test-data.zip";   size = "~1.7GB" }
)

# UA-DETRAC 어노테이션 (Google Drive)
$detracAnnotations = @(
    @{
        # Train XML annotations (vehicle category, weather, scale 등)
        url  = "https://drive.google.com/uc?export=download&id=12xJc8S0Z7lYaAadsi2CoSK3WqH2OkUBu"
        name = "DETRAC-Train_Annotations-XML.zip"
        size = "~15MB"
    },
    @{
        # Test XML annotations
        url  = "https://drive.google.com/uc?export=download&id=1gTMu9ksZr2UUPleDe1yOMqGAJUGx9ByC"
        name = "DETRAC-Train_Annotations-MAT.zip"
        size = "~20MB"
    }
)

foreach ($f in $detracFiles) {
    $filename = Split-Path $f.url -Leaf
    $dest = "$DETRAC_DIR\$filename"
    if (Test-Path $dest) {
        Write-Host "  [SKIP] $filename (already exists)" -ForegroundColor Yellow
    } else {
        Write-Host "  [DOWN] $filename ($($f.size))..." -ForegroundColor Green
        if (Download-FileWithRetry -Url $f.url -Destination $dest) {
            Write-Host "  [DONE] $filename" -ForegroundColor Green
        } else {
            Write-Host "  [FAIL] $filename - Please check your network connection" -ForegroundColor Red
            Write-Host "    URL: $($f.url)" -ForegroundColor Gray
        }
    }
}

foreach ($f in $detracAnnotations) {
    $dest = "$DETRAC_DIR\$($f.name)"
    if (Test-Path $dest) {
        Write-Host "  [SKIP] $($f.name) (already exists)" -ForegroundColor Yellow
    } else {
        Write-Host "  [DOWN] $($f.name) ($($f.size))..." -ForegroundColor Green
        if (Download-FileWithRetry -Url $f.url -Destination $dest) {
            Write-Host "  [DONE] $($f.name)" -ForegroundColor Green
        } else {
            Write-Host "  [FAIL] $($f.name) - Please check your network connection" -ForegroundColor Red
            Write-Host "    URL: $($f.url)" -ForegroundColor Gray
        }
    }
}

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host " Download complete! Extracting archives..." -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan

# --- 압축 해제 ---
function Expand-ZipSafe {
    param([string]$ZipPath, [string]$DestDir)
    $filename = Split-Path $ZipPath -Leaf
    if (Test-Path $ZipPath) {
        Write-Host "  [UNZIP] $filename -> $DestDir" -ForegroundColor Magenta
        Expand-Archive -Path $ZipPath -DestinationPath $DestDir -Force
    }
}

# BDD100K 해제
Expand-ZipSafe "$BDD_DIR\100k_images_train.zip"             $BDD_DIR
Expand-ZipSafe "$BDD_DIR\100k_images_val.zip"               $BDD_DIR
Expand-ZipSafe "$BDD_DIR\bdd100k_det_20_labels_trainval.zip" $BDD_DIR

# UA-DETRAC 해제
Expand-ZipSafe "$DETRAC_DIR\DETRAC-train-data.zip"          $DETRAC_DIR
Expand-ZipSafe "$DETRAC_DIR\DETRAC-test-data.zip"           $DETRAC_DIR
Expand-ZipSafe "$DETRAC_DIR\DETRAC-Train_Annotations-XML.zip" $DETRAC_DIR
Expand-ZipSafe "$DETRAC_DIR\DETRAC-Train_Annotations-MAT.zip" $DETRAC_DIR

Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host " Complete!" -ForegroundColor Green
Write-Host " BDD100K:    $BDD_DIR" -ForegroundColor White
Write-Host " UA-DETRAC:  $DETRAC_DIR" -ForegroundColor White
Write-Host "============================================" -ForegroundColor Green

# --- 최종 디렉토리 구조 확인 ---
Write-Host ""
Write-Host "Directory structure:" -ForegroundColor Cyan
Get-ChildItem $BASE_DIR -Recurse -Depth 2 | Format-Table Mode, Length, Name