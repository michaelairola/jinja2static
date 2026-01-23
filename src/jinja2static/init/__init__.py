import importlib.resources as resources
import logging
import shutil
from pathlib import Path

from jinja2static.config import Config

logger = logging.getLogger(__name__)


def initialize_project(config: Config):
    INIT_DIR = resources.files("jinja2static") / "init"
    templates = INIT_DIR / "templates"
    assets = INIT_DIR / "assets"
    pyproject = INIT_DIR / "pyproject.toml"

    pyproject_file_path = config.project_path / "pyproject.toml"
    if pyproject_file_path.is_file():
        logger.info("pyproject file found. skipping...")
        return

    logger.info(f"Creating '{pyproject_file_path}'")
    shutil.copy(pyproject, pyproject_file_path)
    logger.info(f"Creating '{config.assets}'")
    shutil.copytree(assets, config.assets)
    logger.info(f"Creating '{config.templates}'")
    shutil.copytree(templates, config.templates)
