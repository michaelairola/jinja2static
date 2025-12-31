from __future__ import annotations
import traceback
import logging

from jinja2 import Environment, FileSystemLoader, select_autoescape
from jinja2.exceptions import UndefinedError

from pathlib import Path
from .data import data_functions

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .config import Config

logger = logging.getLogger(__name__)


def build_page(config: Config, filepath: Path) -> bool:
    return_status = True
    config.dist.mkdir(parents=True, exist_ok=True)
    RELATIVE_TO_TEMPLATE_PATH = filepath.relative_to(config.templates)
    DST_FILE_PATH = config.dist / RELATIVE_TO_TEMPLATE_PATH
    data = {}
    for data_func in data_functions:
        try:
            logger.debug(f"getting data from '{data_func.__name__}' with {filepath}")
            data = {**data, **data_func(config, filepath)}
        except Exception as e:
            logging.error(f"Error running data function '{data_func.__name__}': {e}")
    try:
        logger.debug(f"Building '{filepath}' with {data=}")
        rendered_file = (
            Environment(loader=FileSystemLoader(config.templates))
            .get_template(str(RELATIVE_TO_TEMPLATE_PATH))
            .render(config=config, filepath=filepath, **data)
        )
    except UndefinedError as e:
        rendered_file = f"{e}. There is either an undefined variable in the template file, or a data load error occured."
        logger.error(rendered_file)
        return_status = False
    except Exception as e:
        rendered_file = "\n".join([str(e), "-" * 40, traceback.format_exc()])
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
