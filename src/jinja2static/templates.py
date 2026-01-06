from __future__ import annotations
import traceback
import logging

from jinja2 import Environment, FileSystemLoader, meta, Environment
from jinja2.exceptions import UndefinedError, TemplateSyntaxError, TemplateNotFound

from pathlib import Path
# from .data import data_functions

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .config import Config

logger = logging.getLogger(__name__)


def build_page(config: Config, filepath: Path) -> bool:
    return_status = True
    config.dist.mkdir(parents=True, exist_ok=True)
    data = config.data_for(filepath)
    try:
        logger.debug(f"Building '{filepath}' with {data=}")
        rendered_file = (
            Environment(loader=FileSystemLoader(config.templates))
            .get_template(str(filepath))
            .render(config=config, filepath=filepath, **data)
        )
    except UndefinedError as e:
        rendered_file = f"Building '{filepath}': {e}"
        logger.error(rendered_file)
        return_status = False
    except Exception as e:
        rendered_file = "\n".join([str(e), "-" * 40, traceback.format_exc()])
        logger.info(rendered_file)
        logger.error(f"Unable to render '{filepath}'")
        rendered_file = rendered_file.replace("\n", "<br/>")
        return_status = False
    DST_FILE_PATH = config.dist / filepath
    DST_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(DST_FILE_PATH, "w") as f:
        f.write(rendered_file)
    return return_status


def build_pages(config: Config) -> bool:
    return all(build_page(config, page) for page in config.pages)


def find_all_subtemplates(config: Config, template_filepath: Path):
    """
    Recursively finds all templates referenced by the given template.
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

        except TemplateSyntaxError as e:
            logger.error(f"Unable to process template: {e}")
            continue
        except TemplateNotFound:
            logger.warning(f"Referenced template '{current_template_name}' not found.")
            continue

    # Remove the initial template from the result set if you only want subtemplates
    found_templates.discard(template_name)
    return found_templates
