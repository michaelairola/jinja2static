import os
import shutil
from pathlib import Path


def rm_file_if_exists(file_path: Path):
    if file_path.exists():
        if file_path.is_dir():
            shutil.rmtree(file_path)
        else:
            os.remove(file_path)
