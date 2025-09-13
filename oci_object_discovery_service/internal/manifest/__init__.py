import yaml
from pathlib import Path

def load_from_file(path: str):
    data = yaml.safe_load(Path(path).read_text())
    return data.get("jobs", [])
