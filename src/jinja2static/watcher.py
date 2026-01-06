import logging
import os
from functools import wraps
from asyncio import create_task, sleep
import time

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
    logger.info(f"Rebuilding {[str(file) for file in files_to_rebuild]}...")
    for file_path in files_to_rebuild:
        build_page(config, file_path)
    end_time = time.perf_counter()
    logger.info(f"Rebuilt in {(end_time - start_time):.4f} seconds")


@watch_for_file_changes
def detect_changes_copy_asset(file_path, config):
    copy_asset_file(config, file_path.relative_to(config.assets))

@watch_for_file_changes
def detect_changes_yaml_data_files(file_path, config):
    start_time = time.perf_counter()    
    config.data_module.update_yaml_data()
    effected_templates_dir = config.templates / config.data_module.relative_path
    files_to_rebuild = list(effected_templates_dir.rglob("*"))
    files_to_rebuild = [
        page.relative_to(config.templates) for page in files_to_rebuild 
        if page.relative_to(config.templates) in config.pages
    ]
    logger.info(f"Rebuilding {[str(file) for file in files_to_rebuild]}...")
    for file_path in files_to_rebuild:
        build_page(config, file_path)
    end_time = time.perf_counter()
    logger.info(f"Rebuilt in {(end_time - start_time):.4f} seconds")

@watch_for_file_changes
def detect_changes_pymod_data_files(file_path, config):
    start_time = time.perf_counter()    
    config.data_module.update_module_data()
    effected_templates_dir = config.templates / config.data_module.relative_path
    files_to_rebuild = list(effected_templates_dir.rglob("*"))
    files_to_rebuild = [
        page.relative_to(config.templates) for page in files_to_rebuild 
        if page.relative_to(config.templates) in config.pages
    ]
    logger.info(f"Rebuilding {[str(file) for file in files_to_rebuild]}...")
    for file_path in files_to_rebuild:
        build_page(config, file_path)
    end_time = time.perf_counter()
    logger.info(f"Rebuilt in {(end_time - start_time):.4f} seconds")

def file_watcher(config: Config):
    for file_path in config.templates.rglob("*"):
        create_task(detect_template_changes_build_index(file_path, config))
    for file_path in config.assets.rglob("*"):
        create_task(detect_changes_copy_asset(file_path, config))
    
    py_mod_file_path = config.data_module.python_module_file_path
    if py_mod_file_path:
        create_task(
            detect_changes_pymod_data_files(
                py_mod_file_path,
                config
            )
        )
    yaml_file_path = config.data_module.yaml_file_path
    if yaml_file_path:
        create_task(
            detect_changes_yaml_data_files(
                yaml_file_path,
                config
            )
        )
