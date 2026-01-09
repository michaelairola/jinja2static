import logging
import os
import time
from asyncio import create_task, gather, CancelledError
from functools import wraps
from pathlib import Path
from watchfiles import awatch, Change

from .assets import copy_asset_file
from .config import Config
from .templates import build_page

logger = logging.getLogger(__name__)


def watch_for_file_changes(func):
    @wraps(func)
    async def wrapper(dir_path: Path, *args, **kwargs):
        async for changes in awatch(dir_path):
            for change, file_path in changes:
                file_path=Path(file_path)
                match change:
                    case Change.modified:
                        logger.info(f"File '{file_path}' has changed...")
                        func(file_path, *args, **kwargs)
                    case Change.added:
                        if file_path.exists():
                            logger.info(f"New file '{file_path}' has been created...")
                            func(file_path, *args, **kwargs)
                    case Change.deleted:
                        logger.info(f"File '{file_path}' has been deleted...")
                    case _:
                        logger.warning(f"File change '{change.name}' not registered.")
    return wrapper


@watch_for_file_changes
def detect_template_changes_build_index(file_path, config):
    start_time = time.perf_counter()
    file_path = file_path.relative_to(config.templates.absolute())
    config.update_dependency_graph(file_path)
    files_to_rebuild = config.get_dependencies(file_path)
    if file_path in config.pages:
        files_to_rebuild.add(file_path)
    logger.info(f"Rebuilding {[str(file) for file in files_to_rebuild]}...")
    for file_path in files_to_rebuild:
        build_page(config, file_path)
    end_time = time.perf_counter()
    logger.info(f"Rebuilt in {(end_time - start_time):.4f} seconds")


@watch_for_file_changes
def detect_changes_copy_asset(file_path, config):
    copy_asset_file(config, file_path.relative_to(config.assets))


def detect_changes_data_files(file_path, config, callback_fn):
    @watch_for_file_changes
    def x(file_path, config):
        start_time = time.perf_counter()
        callback_fn()
        effected_templates_dir = config.templates / config.data_module.relative_path
        files_to_rebuild = list(effected_templates_dir.rglob("*"))
        files_to_rebuild = [
            page.relative_to(config.templates)
            for page in files_to_rebuild
            if page.relative_to(config.templates) in config.pages
        ]
        logger.info(f"Rebuilding {[str(file) for file in files_to_rebuild]}...")
        for file_path in files_to_rebuild:
            build_page(config, file_path)
        end_time = time.perf_counter()
        logger.info(f"Rebuilt in {(end_time - start_time):.4f} seconds")

    return x(file_path, config)


async def file_watcher(config: Config):
    logger.info(f"Watching for file changes in '{config.project_path}'...")
    tasks = []
    tasks.append(create_task(detect_template_changes_build_index(config.templates, config)))
    tasks.append(create_task(detect_changes_copy_asset(config.assets, config)))
    data_mod = config.data_module
    pymod_path = data_mod.python_module_file_path
    if pymod_path:
        tasks.append(create_task(detect_changes_data_files(pymod_path, config, data_mod.update_module_data)))
    yaml_path = data_mod.yaml_file_path
    if yaml_path:
        tasks.append(create_task(detect_changes_data_files(yaml_path, config, data_mod.update_yaml_data)))
    await gather(*tasks)

