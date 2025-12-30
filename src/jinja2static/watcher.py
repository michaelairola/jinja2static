from .templates import build_page
from .assets import copy_asset_file
from functools import wraps

from .config import Config


def watch_for_file_changes(func):
    @wraps(func)
    async def wrapper(file_path, *args, **kwargs):
        last_modified = os.path.getmtime(file_path)
        while True:
            current_modified = os.path.getmtime(file_path)
            if current_modified != last_modified:
                logger.info(f"File '{file_path.name}' has changed...")
                func(file_path, *args, **kwargs)
                logger.info(
                    f"Rebuilt '{file_path.name}' @ {datetime.fromtimestamp(current_modified)}"
                )
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
def detect_changes_copy_asset(file_path, config):
    copy_asset_file(config, file_path)


def file_watcher(config: Config):
    graph = dependency_graph(config)
    for file_path in config.templates.rglob("*"):
        create_task(detect_changes_build_index(file_path, config, graph))
    for file_path in config.assets.rglob("*"):
        create_task(detect_changes_copy_asset(file_path, config))
