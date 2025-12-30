import os
from pathlib import Path
import shutil
from functools import wraps
from asyncio import create_task, sleep
from datetime import datetime
import logging
import traceback

from jinja2 import Environment, FileSystemLoader, select_autoescape
from jinja2.exceptions import UndefinedError

from .meta import dependency_graph
from .config import Config
from .data import data_functions

logger = logging.getLogger(__name__)

def rm_file_if_exists(file_path: Path):
    if file_path.exists():
        if file_path.is_dir():
            shutil.rmtree(file_path)
        else:
            os.remove(file_path)

def build_page(config: Config, filepath: Path) -> bool:
    logger.debug(f"Building '{filepath}'...")
    return_status = True
    config.dist.mkdir(parents=True, exist_ok=True)
    RELATIVE_TO_TEMPLATE_PATH = filepath.relative_to(config.templates)
    DST_FILE_PATH = config.dist / RELATIVE_TO_TEMPLATE_PATH
    rm_file_if_exists(DST_FILE_PATH)
    data = {}
    for data_func in data_functions:
        try:
            logger.debug(f"getting data from '{data_func.__name__}' with {filepath}")
            data = { **data, **data_func(config, filepath) }
        except Exception as e:
            logging.error(f"Error running data function '{data_func.__name__}': {e}")
    try:
        logger.debug(f"rendering {filepath} with {data=}")
        rendered_file = Environment(loader=FileSystemLoader(config.templates))\
            .get_template(str(RELATIVE_TO_TEMPLATE_PATH))\
            .render(
                config=config,
                filepath=filepath,
                **data
            )
    except UndefinedError as e:
        rendered_file = f"{e}. There is either an undefined variable in the template file, or a data load error occured."
        logger.error(rendered_file)
        return_status = False
    except Exception as e:
        rendered_file = "\n".join([ 
            str(e), 
            "-"*40, 
            traceback.format_exc() 
        ])
        logger.info(rendered_file)
        logger.error(f"Unable to render '{filepath}'")
        rendered_file = rendered_file.replace("\n", "<br/>")
        return_status = False
    DST_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(DST_FILE_PATH, "w") as f:
        f.write(rendered_file)
    return return_status

def build_pages(config: Config) -> bool:
    return all(build_page(config, page) for page in config.pages)

def copy_static_dir(config: Config):
    config.dist.mkdir(parents=True, exist_ok=True)
    DST = config.dist / "static"
    rm_file_if_exists(DST)
    shutil.copytree(config.assets, DST)


def build(config: Config | None, verbose: bool=False) -> bool:
    if not config:
        return False
    rm_file_if_exists(config.dist)
    logger.info("Building...")
    copy_static_dir(config)
    if build_pages(config):
        logger.info("Successfully built.")
    return True


def copy_static_file(config: Config, file_path: str):
    config.dist.mkdir(parents=True, exist_ok=True)
    DST = config.dist / "static" / file_path.name
    rm_file_if_exists(DST)
    shutil.copy(file_path, DST)


def watch_for_file_changes(func):
    @wraps(func)
    async def wrapper(file_path, *args, **kwargs):
        last_modified = os.path.getmtime(file_path)
        while True:
            current_modified = os.path.getmtime(file_path)
            if current_modified != last_modified:
                logger.info(f"File '{file_path.name}' has changed...")
                func(file_path, *args, **kwargs)
                logger.info(f"Rebuilt '{file_path.name}' @ {datetime.fromtimestamp(current_modified)}")
                last_modified = current_modified
            await sleep(1)

    return wrapper


@watch_for_file_changes
def detect_changes_build_index(file_path, config, graph):
    if file_path in config.pages:
        build_page(config, file_path)
    parent_files = graph.get(file_path.name, [])
    for parent_file in parent_files:
        build_page(config, parent_file)


@watch_for_file_changes
def detect_changes_copy_static_file(file_path, config):
    copy_static_file(config, file_path)


def file_watcher(config: Config):
    graph = dependency_graph(config)
    for file_path in config.templates.rglob("*"):
        create_task(detect_changes_build_index(file_path, config, graph))
    for file_path in config.assets.rglob("*"):
        create_task(detect_changes_copy_static_file(file_path, config))
