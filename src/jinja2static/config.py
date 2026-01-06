from pathlib import Path
from dataclasses import dataclass, field
import logging
from collections import defaultdict

try:
    import tomllib
except ImportError:
    # Python < 3.11
    import tomli as tomllib

from .data import DataModule
from .templates import find_all_subtemplates

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
            "data": project_path / "data",
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
        for page in config.pages:
            config.update_dependency_graph(page)
        return config

    def __post_init__(self):
        self.data_module = DataModule(config=self, module_path=self.data)

    @property
    def pages(self) -> list[str]:
        return [
            p.relative_to(self.templates)
            for p in Path(self.templates).rglob("*")
            if p.is_file() and not p.name.startswith("_")
        ]

    _parent_to_child_graph = {}

    def update_dependency_graph(self, file_path: Path):
        self._parent_to_child_graph[file_path] = find_all_subtemplates(self, file_path)

    @property
    def dependency_graph(self):
        child_to_parent = defaultdict(set)
        for original_key, value_set in self._parent_to_child_graph.items():
            for value in value_set:
                child_to_parent[Path(value)].add(original_key)
        return dict(child_to_parent)

    def get_dependencies(self, file_path: Path) -> list[str, Path]:
        return self.dependency_graph.get(file_path, set())

    def data_for(self, file_path: Path):
        return self.data_module.data_for(file_path)
