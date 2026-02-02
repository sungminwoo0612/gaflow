#!/usr/bin/env bash
# =============================================================================
# GAFlow Conda 환경 생성 및 의존성 일괄 셋업 (POSIX Bash)
# - conda 환경 생성/갱신, pip 의존성 설치, 환경 검증
# =============================================================================

set -euo pipefail

DRY_RUN=false
VERBOSE=false
RECREATE=false

# --- 경로: 스크립트 기준 프로젝트 루트 ---
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
CONDA_YAML="$PROJECT_ROOT/conda.yaml"

# --- 정리 트랩 ---
cleanup() {
  local r=$?
  if [ $r -ne 0 ]; then
    echo "[ERROR] Setup failed (exit $r)." >&2
  fi
  popd >/dev/null 2>&1 || true
}
trap cleanup EXIT

usage() {
  echo "Usage: $0 [OPTIONS]"
  echo "  --dry-run    Print commands only, do not execute"
  echo "  --verbose    Verbose output"
  echo "  --recreate   Remove existing env and create fresh"
  echo "  -h, --help   This help"
}

for arg in "$@"; do
  case "$arg" in
    --dry-run)   DRY_RUN=true ;;
    --verbose)   VERBOSE=true ;;
    -v)          VERBOSE=true ;;
    --recreate)  RECREATE=true ;;
    -h|--help)   usage; exit 0 ;;
    *)           echo "Unknown option: $arg"; usage; exit 1 ;;
  esac
done

log_verbose() {
  $VERBOSE && echo "[VERBOSE] $*" >&2
}

# --- Conda 사용 가능 여부 확인 ---
check_conda() {
  if ! command -v conda >/dev/null 2>&1; then
    echo "[ERROR] conda not found. Install Miniconda/Anaconda and add to PATH." >&2
    return 1
  fi
  log_verbose "conda found."
  return 0
}

# --- conda.yaml 존재 확인 ---
check_conda_yaml() {
  if [ ! -f "$CONDA_YAML" ]; then
    echo "[ERROR] conda.yaml not found: $CONDA_YAML" >&2
    return 1
  fi
  log_verbose "conda.yaml: $CONDA_YAML"
  return 0
}

# --- 환경 이름 추출 (conda.yaml 첫 줄 name: xxx) ---
get_env_name() {
  local line
  line=$(sed -n '1p' "$CONDA_YAML")
  if [[ "$line" =~ ^[[:space:]]*name:[[:space:]]*(.+)$ ]]; then
    echo "${BASH_REMATCH[1]}" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//'
  else
    echo "gaflow"
  fi
}

# --- 환경 존재 여부 ---
env_exists() {
  local name="$1"
  conda env list 2>/dev/null | awk 'NF && $0 !~ /^#/ {print $1}' | grep -qxF "$name"
}

# --- 환경 생성 ---
create_env() {
  local name="$1"
  if $DRY_RUN; then
    echo "[DRY-RUN] conda env create -f \"$CONDA_YAML\""
    return 0
  fi
  echo "[CREATE] Creating conda env: $name from conda.yaml"
  pushd "$PROJECT_ROOT" >/dev/null
  conda env create -f "$CONDA_YAML"
  popd >/dev/null
}

# --- 환경 갱신 ---
update_env() {
  local name="$1"
  if $DRY_RUN; then
    echo "[DRY-RUN] conda env update -f \"$CONDA_YAML\" --prune"
    return 0
  fi
  echo "[UPDATE] Updating conda env: $name from conda.yaml"
  pushd "$PROJECT_ROOT" >/dev/null
  conda env update -f "$CONDA_YAML" --prune
  popd >/dev/null
}

# --- 환경 제거 ---
remove_env() {
  local name="$1"
  if $DRY_RUN; then
    echo "[DRY-RUN] conda env remove -n $name -y"
    return 0
  fi
  echo "[REMOVE] Removing env: $name"
  conda env remove -n "$name" -y
}

# --- 환경 검증 ---
verify_env() {
  local name="$1"
  if $DRY_RUN; then
    echo "[DRY-RUN] Would run: conda run -n $name python -c \"import mlflow; import ultralytics\""
    return 0
  fi
  echo "[VERIFY] Checking imports in env: $name"
  if ! conda run -n "$name" python -c "import mlflow; import ultralytics; print('OK')"; then
    echo "[ERROR] Verification failed." >&2
    return 1
  fi
  return 0
}

# --- 메인 ---
main() {
  echo "============================================"
  echo " GAFlow environment setup"
  echo "============================================"

  check_conda    || exit 1
  check_conda_yaml || exit 1

  ENV_NAME=$(get_env_name)

  if $RECREATE && env_exists "$ENV_NAME"; then
    remove_env "$ENV_NAME" || exit 1
  fi

  if ! env_exists "$ENV_NAME"; then
    create_env "$ENV_NAME" || exit 1
  else
    update_env "$ENV_NAME" || exit 1
  fi

  verify_env "$ENV_NAME" || exit 1

  echo ""
  echo "============================================"
  echo " Setup complete."
  echo " Activate: conda activate $ENV_NAME"
  echo "============================================"
}

main
