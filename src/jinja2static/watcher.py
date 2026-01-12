import logging
import os
import time
from asyncio import CancelledError, create_task, gather
from functools import wraps
from pathlib import Path

from watchfiles import Change, awatch

from .assets import copy_asset_file
from .config import Config
from .templates import build_page

logger = logging.getLogger(__name__)

def template_file_update(config: Config, file_path: Path):
    start_time = time.perf_counter()
    config.update_dependency_graph(file_path)
    files_to_rebuild = config.get_dependencies(file_path)
    if file_path in config.pages:
        files_to_rebuild.add(file_path)
    logger.info(f"Rebuilding {[str(file.relative_to(config.templates)) for file in files_to_rebuild]}...")
    for file_path in files_to_rebuild:
        build_page(config, file_path)
    end_time = time.perf_counter()
    logger.info(f"Rebuilt in {(end_time - start_time):.4f} seconds")

def detect_changes_copy_asset(config: Config, file_path: Path):
    copy_asset_file(config, file_path.relative_to(config.assets))

def data_file_update(config: Config, file_path: Path):
    start_time = time.perf_counter()
    config.data_module.update(file_path)
    files_to_rebuild = config.data_module.effected_pages(file_path)
    logger.info(f"Rebuilding {[str(file.relative_to(config.templates)) for file in files_to_rebuild]}...")
    for file_path in files_to_rebuild:
        build_page(config, file_path)
    end_time = time.perf_counter()
    logger.info(f"Rebuilt in {(end_time - start_time):.4f} seconds")

def tbd(_: Config, _x: Path): 
    logger.warning("TBD")
    return

def update_project_callback(config: Config, file_path: Path):
    if config.templates in file_path.parents:
        return template_file_update, tbd
    if config.assets in file_path.parents:
        return detect_changes_copy_asset, tbd
    if file_path in config.data_module:
        return data_file_update, tbd
    return None, None

async def file_watcher(config: Config):
    logger.info(f"Watching for file changes in '{config.project_path}'...")
    async for changes in awatch(config.project_path):
        for change, file_path in changes:
            file_path = Path(file_path)
            file_path_str = file_path.relative_to(config.project_path)
            update_fn, delete_fn = update_project_callback(config, file_path)
            if not update_fn:
                continue
            match change:
                case Change.modified | Change.added:
                    msg = f"File '{file_path_str}' has changed..." if change == Change.modified else f"New file '{file_path_str}' has been created..."
                    logger.info(msg)
                    update_fn(config, file_path)
                case Change.deleted:
                    logger.info(f"File '{file_path_str}' has been deleted...")
                    delete_fn(config, file_path)
                case _:
                    logger.warning(f"File change '{change.name}' not registered.")
