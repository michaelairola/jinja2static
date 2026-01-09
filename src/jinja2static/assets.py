from __future__ import annotations

import logging
import shutil
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .config import Config

logger = logging.getLogger(__name__)


def copy_asset_dir(config: Config):
    logger.info(f"Copying assets '{config.assets}' => '{config.dist}'")
    config.dist.mkdir(parents=True, exist_ok=True)
    shutil.copytree(config.assets, config.dist, dirs_exist_ok=True)


def copy_asset_file(config: Config, file_path: str):
    config.dist.mkdir(parents=True, exist_ok=True)
    src_file_path = config.assets / file_path
    dst_file_path = config.dist / file_path
    shutil.copy(src_file_path, dst_file_path)
    logger.info(
        f"Copied '{src_file_path.relative_to(config.project_path)}' -> {dst_file_path.relative_to(config.project_path)}"
    )
