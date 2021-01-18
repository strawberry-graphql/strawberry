import os
from pathlib import Path


all_files = Path(os.environ["HOME"]) / "files.json"

with all_files.open() as f:
    print(f.read())
