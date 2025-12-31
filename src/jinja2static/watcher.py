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


def find_all_subtemplates(config: Config, template_filepath: Path):
    """
    Recursively finds all templates referenced by the given template.

    :param env: The Jinja2 Environment instance.
    :param template_name: The name of the starting template.
    :return: A set of all referenced template names.
    """
    template_name = str(template_filepath)
    env = Environment(loader=FileSystemLoader(config.templates))
    found_templates = set()
    unprocessed_templates = {template_name}
    while unprocessed_templates:
        current_template_name = unprocessed_templates.pop()
        if current_template_name in found_templates:
            continue

        # Add to the set of processed templates
        found_templates.add(current_template_name)

        try:
            # Get the source and AST (Abstract Syntax Tree)
            source, filename, uptodate = env.loader.get_source(
                env, current_template_name
            )
            ast = env.parse(source)

            # Find all templates referenced in the current AST
            referenced = meta.find_referenced_templates(ast)

            # Add new, unprocessed templates to the queue
            for ref in referenced:
                if ref is not None and ref not in found_templates:
                    unprocessed_templates.add(ref)

        except jinja2.exceptions.TemplateSyntaxError as e:
            logger.error(f"Unable to process template: {e}")
            continue
        except jinja2.exceptions.TemplateNotFound:
            logger.warning(f"Referenced template '{current_template_name}' not found.")
            continue

    # Remove the initial template from the result set if you only want subtemplates
    found_templates.discard(template_name)
    return found_templates


def dependency_graph(config: Config):
    parent_to_child = {
        page: find_all_subtemplates(config, page) for page in config.pages
    }
    child_to_parent = defaultdict(set)
    for original_key, value_set in parent_to_child.items():
        for value in value_set:
            child_to_parent[value].add(original_key)
    return dict(child_to_parent)


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
def detect_template_changes_build_index(file_path, config, graph):
    file_path = file_path.relative_to(config.templates)
    start_time = time.perf_counter()
    files_to_rebuild = graph.get(file_path.name, [])
    if file_path in config.pages:
        files_to_rebuild.append(file_path)
    logger.info(f"Rebuilding {[ str(file) for file in files_to_rebuild ]}...")
    for file_path in files_to_rebuild:
        build_page(config, file_path)
    end_time = time.perf_counter()
    logger.info(f"Rebuilt in {(end_time - start_time):.4f} seconds")


@watch_for_file_changes
def detect_changes_copy_asset(file_path, config):
    copy_asset_file(config, file_path.relative_to(config.assets))


def file_watcher(config: Config):
    graph = dependency_graph(config)
    for file_path in config.templates.rglob("*"):
        create_task(detect_template_changes_build_index(file_path, config, graph))
    for file_path in config.assets.rglob("*"):
        create_task(detect_changes_copy_asset(file_path, config))
