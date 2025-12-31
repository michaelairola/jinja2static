from pathlib import Path
from dataclasses import dataclass, field
import logging
import importlib
import sys
from collections import defaultdict

from jinja2 import meta, FileSystemLoader, Environment

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
        for page in config.pages:
            config.update_dependency_graph(page)
        load_data_module(config)
        return config

    @property
    def pages(self) -> list[str]:
        return [
            p.relative_to(self.templates)
            for p in Path(self.templates).rglob("*")
            if p.is_file() and not p.name.startswith("_")
        ]

    def find_all_subtemplates(self, template_filepath: Path):
        """
        Recursively finds all templates referenced by the given template.

        :param env: The Jinja2 Environment instance.
        :param template_name: The name of the starting template.
        :return: A set of all referenced template names.
        """
        template_name = str(template_filepath)
        env = Environment(loader=FileSystemLoader(self.templates))
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

    _parent_to_child_graph = {}
    def update_dependency_graph(self, file_path: Path):
        self._parent_to_child_graph[file_path] = self.find_all_subtemplates(file_path)
    
    @property
    def dependency_graph(self):
        child_to_parent = defaultdict(set)
        for original_key, value_set in self._parent_to_child_graph.items():
            for value in value_set:
                child_to_parent[Path(value)].add(original_key)
        return dict(child_to_parent)

    def get_dependencies(self, file_path: Path) -> list[str, Path]:
        return self.dependency_graph.get(file_path, set())
