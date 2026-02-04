"""lab 실험 공통: 데이터 YAML 경로 해석."""
from pathlib import Path


def resolve_data_yaml(data_path: str, base_dir: Path) -> Path:
    """data_path(디렉터리 또는 yaml 파일)에서 YOLO data yaml 경로 반환."""
    p = Path(data_path)
    if not p.is_absolute():
        p = (base_dir / p).resolve()
    if p.suffix.lower() in (".yaml", ".yml"):
        return p if p.exists() else p
    for name in ("data.yaml", "dataset.yaml", "train.yaml"):
        candidate = p / name
        if candidate.exists():
            return candidate
    for f in p.rglob("*.yaml"):
        if "data" in f.stem.lower() or f.name == "dataset.yaml":
            return f
    return p / "data.yaml"
