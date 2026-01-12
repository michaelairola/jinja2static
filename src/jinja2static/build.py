import logging
import shutil
import time

from .assets import copy_asset_dir
from .config import Config
from .templates import build_pages

logger = logging.getLogger(__name__)


def build(config: Config | None) -> bool:
    if not config:
        return False
    if config.dist.exists():
        logger.debug(f"Removing '{config.dist}'")
        shutil.rmtree(config.dist)
    start_time = time.perf_counter()
    logger.info("Building...")
    copy_asset_dir(config)
    if not build_pages(config):
        return False
    end_time = time.perf_counter()
    logger.info(f"Successfully built in {(end_time - start_time):.4f} seconds.")
    return True
