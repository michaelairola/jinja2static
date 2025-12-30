from pathlib import Path
from dataclasses import dataclass, field
import logging
import importlib
import sys

try:
    import tomllib
except ImportError:
    # Python < 3.11
    import tomli as tomllib

from .data import load_data_module

logger = logging.getLogger(__name__)


@dataclass
class Config:
    project_path: Path = field()
    templates: Path = field()
    assets: Path = field()
    dist: Path = field()
    data: Path = field()

    @classmethod
    def from_(cls, file_path_str: str | None = None):
        logger.debug(f"Configuring project with '{file_path_str}'")
        file_path = Path(file_path_str) if file_path_str else Path.cwd()
        if not file_path.exists():
            logger.error(f"File Path '{file_path}' does not exist")
            return None
        if file_path.is_dir():
            logger.debug(f"Filepath '{file_path}' is a directory.")
            project_path = file_path
            pyproject_path = file_path / "pyproject.toml"
        else:
            logger.debug(f"Filepath '{file_path}' is a configuration file.")
            project_path = file_path.parent
            pyproject_path = file_path

        pyproject_data = {}
        try:
            with open(pyproject_path, "rb") as f:
                pyproject_data = tomllib.load(f)
        except FileNotFoundError:
            logger.debug(
                f"No pyproject.toml file found at {file_path}. Using default values."
            )
        except tomllib.TOMLDecodeError as e:
            logger.error(f"Unable to decoding TOML file: {e}")
            return None
        default_config_data = {
            "templates": project_path / "templates",
            "assets": project_path / "assets",
            "dist": project_path / "dist",
            "data": project_path / "data.py",
        }
        config_data = pyproject_data.get("tools", {}).get("jinja2static", {})
        config_data = {
            k: project_path / Path(v)
            for k, v in config_data.items()
            if k in [k for k in cls.__dataclass_fields__.keys()]
        }
        kwargs = {**default_config_data, **config_data}
        logger.debug(f"Config data loaded: {kwargs}")
        config = cls(project_path=project_path, **kwargs)
        load_data_module(config)
        return config

    @property
    def pages(self) -> list[str]:
        return [
            p
            for p in Path(self.templates).rglob("*")
            if p.is_file() and not p.name.startswith("_")
        ]
