from __future__ import annotations
from typing import TYPE_CHECKING
import shutil

from .files import rm_file_if_exists

if TYPE_CHECKING:
    from .config import Config


def copy_asset_dir(config: Config):
    config.dist.mkdir(parents=True, exist_ok=True)
    DST = config.dist / "static"
    rm_file_if_exists(DST)
    shutil.copytree(config.assets, DST)


def copy_asset_file(config: Config, file_path: str):
    config.dist.mkdir(parents=True, exist_ok=True)
    DST = config.dist / "static" / file_path.name
    rm_file_if_exists(DST)
    shutil.copy(file_path, DST)
