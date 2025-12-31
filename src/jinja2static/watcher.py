import logging
import os
from datetime import datetime
from functools import wraps
from pathlib import Path
from collections import defaultdict
from asyncio import create_task, sleep
from asyncio.exceptions import CancelledError
import time

import jinja2
from jinja2 import meta, FileSystemLoader, Environment

from .templates import build_page
from .assets import copy_asset_file
from .config import Config

logger = logging.getLogger(__name__)

def watch_for_file_changes(func):
    @wraps(func)
    async def wrapper(file_path, *args, **kwargs):
        last_modified = os.path.getmtime(file_path)
        while True:
            current_modified = os.path.getmtime(file_path)
            if current_modified != last_modified:
                logger.info(f"File '{file_path}' has changed...")
                func(file_path, *args, **kwargs)
                last_modified = current_modified
            await sleep(1)
    return wrapper


@watch_for_file_changes
def detect_template_changes_build_index(file_path, config):
    start_time = time.perf_counter()
    file_path = file_path.relative_to(config.templates)
    config.update_dependency_graph(file_path)
    files_to_rebuild = config.get_dependencies(file_path)
    if file_path in config.pages:
        files_to_rebuild.add(file_path)
    logger.info(f"Rebuilding {[ str(file) for file in files_to_rebuild ]}...")
    for file_path in files_to_rebuild:
        build_page(config, file_path)
    end_time = time.perf_counter()
    logger.info(f"Rebuilt in {(end_time - start_time):.4f} seconds")


@watch_for_file_changes
def detect_changes_copy_asset(file_path, config):
    copy_asset_file(config, file_path.relative_to(config.assets))


def file_watcher(config: Config):
    for file_path in config.templates.rglob("*"):
        create_task(detect_template_changes_build_index(file_path, config))
    for file_path in config.assets.rglob("*"):
        create_task(detect_changes_copy_asset(file_path, config))
