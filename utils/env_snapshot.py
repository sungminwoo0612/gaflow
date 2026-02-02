"""
실험 재현성을 위한 환경 스냅샷: pip/conda 목록 + git 정보를 MLflow에 기록.
"""
import subprocess
import sys
from pathlib import Path
from typing import Any

import mlflow


def _run(cmd: list[str], cwd: Path | None = None) -> tuple[str, int]:
    try:
        out = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,
            cwd=cwd,
        )
        return (out.stdout or "") + (out.stderr or ""), out.returncode
    except Exception as e:
        return str(e), -1
