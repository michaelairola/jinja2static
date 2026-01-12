from __future__ import annotations

import importlib
import inspect
import logging
import os
import sys
import traceback
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import TYPE_CHECKING

import yaml

if TYPE_CHECKING:
    from pathlib import Path

    from jinja2static.config import Config

logger = logging.getLogger(__name__)


class JinjaDataFunction(Enum):
    """An enumeration of colors."""

    GLOBAL = auto()
    PER_PAGE = auto()


def global_data(func):
    func.jinja2static = JinjaDataFunction.GLOBAL
    return func


def per_page_data(func):
    func.jinja2static = JinjaDataFunction.PER_PAGE
    return func


def load_pymod(file_path: Path):
    suffix = ".__init__.py" if file_path.name == "__init__.py" else ".py"
    module_name = str(file_path).replace("/", ".").removesuffix(suffix)
    logger.debug(f"Loading module '{module_name}' from '{file_path}'")
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if not spec or not spec.loader:
        logger.warning(f"Could not find module spec for '{module_name}'")
        return None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
    except Exception as e:
        logger.error(f"importing dynamic module '{module_name}': {e}")
    return module


def get_callback_functions(data_module: DataModule):
    data_functions = {JinjaDataFunction.GLOBAL: [], JinjaDataFunction.PER_PAGE: []}
    file_path = data_module.pymod_file_path
    if not file_path:
        return data_functions
    module = load_pymod(file_path)
    if not module:
        return data_functions
    all_functions = [f for (_, f) in inspect.getmembers(module, inspect.isfunction)]
    for function in all_functions:
        func_type = getattr(function, "jinja2static", None)
        if not func_type:
            continue
        data_functions[func_type].append(function)
    return data_functions


@dataclass
class DataModule:
    config: Config = field()
    file_path: Path = field()

    submodules = []

    def __post_init__(self):
        if not self.pymod_file_path or self.file_path.is_file():
            return
        logger.debug(f"Getting subpaths for {self.file_path}")
        subpaths = [
            file_path
            for file_path in self.file_path.iterdir()
            if file_path.suffix == ".py"
            and file_path != self.pymod_file_path
            and file_path != self.yaml_file_path
            and file_path.name != "__pycache__"  # TODO: make this more robust
        ]
        logger.debug(f"Recursing through {[path.name for path in subpaths]}")
        self.submodules = [
            DataModule(config=self.config, file_path=file_path)
            for file_path in subpaths
        ]

    _functions = {}

    @property
    def functions(self):
        if not self._functions:
            self.update_functions()
        return self._functions

    def update_functions(self):
        self._functions = get_callback_functions(self)

    _yaml_data = {}

    @property
    def yaml_data(self):
        if not self._yaml_data:
            self.update_yaml_data()
        return self._yaml_data

    def update_yaml_data(self) -> bool:
        if not self.yaml_file_path:
            return False
        logger.debug(f"Getting yaml data from '{self.yaml_file_path}'")
        with open(self.yaml_file_path, "r") as stream:
            try:
                self._yaml_data = yaml.safe_load(stream)
                return True
            except yaml.YAMLError as exc:
                logger.error(f"YAML file {self.yaml_file_path}'")
                logger.info(exc)
                return False

    _global_data = {}

    @property
    def global_data(self):
        if not self._global_data:
            self.update_pymod_data()
        return self._global_data

    def update_pymod_data(self):
        self.update_functions()
        self._global_data = {}
        for f in self.functions[JinjaDataFunction.GLOBAL]:
            try:
                self._global_data = {
                    **self._global_data,
                    **f(self._global_data, self.config),
                }
            except Exception as e:
                logger.error(f"{e}")
                logger.info(traceback.format_exc())

    def per_file_data(self, file_path: Path):
        per_file_data = {}
        for f in self.functions[JinjaDataFunction.PER_PAGE]:
            try:
                per_file_data = {
                    **per_file_data,
                    **f(per_file_data, self.config, file_path),
                }
            except Exception as e:
                logger.error(f"{e}")
                logger.info(traceback.format_exc())
        return per_file_data

    @property
    def pymod_file_path(self):
        file_path = self.file_path
        file_path_py = file_path.with_suffix(".py")
        if file_path_py.exists():
            return file_path_py
        if file_path.is_dir():
            file_path = file_path / "__init__.py"
            if file_path.exists():
                return file_path
        return None

    @property
    def yaml_file_path(self):
        file_path = self.file_path
        possible_yamls = [
            file_path.with_suffix(".yaml"),
            file_path.with_suffix(".yml"),
            file_path / "__init__.yaml",
            file_path / "__init__.yml",
        ]
        for file_path in possible_yamls:
            if file_path.exists():
                return file_path
        return None

    def is_data_file_path(self, file_path: Path):
        if self.pymod_file_path == file_path:
            return True
        if self.yaml_file_path == file_path:
            return True
        return False

    def __contains__(self, file_path: Path):
        return self.is_data_file_path(file_path) or file_path.is_relative_to(
            self.config.data
        )

    def get_update_function_for(self, file_path: Path):
        logger.debug(f"file: '{file_path}', yaml: '{self.yaml_file_path}'")
        if self.pymod_file_path == file_path:
            return self.update_pymod_data
        if self.yaml_file_path == file_path:
            return self.update_yaml_data
        logger.warning(
            f"Data file '{file_path}' not registred as a valid data file for '{self.file_path}'."
        )
        logger.warning(
            f"pymod file: {self.pymod_file_path}, yaml: {self.yaml_file_path}"
        )
        return False

    def get_data_mod_for(self, file_path: Path):
        if self.is_data_file_path(file_path):
            return self
        return (
            next(submod.get_data_mod_for(file_path) for submod in self.submodules)
            if self.submodules
            else None
        )

    def effects_template_file(self, file_path: Path) -> bool:
        data_file_path = (
            self.config.data / file_path.relative_to(self.config.templates)
        ).with_suffix("")
        return self.file_path.with_suffix("") in [
            data_file_path,
            *data_file_path.parents,
        ]

    def update(self, file_path: Path) -> list[Path]:
        if not file_path in self:
            return
        data_mod = self.get_data_mod_for(file_path)
        update_fn = data_mod.get_update_function_for(file_path)
        if update_fn:
            return update_fn()
        return [
            page for page in self.config.pages if data_mod.effects_template_file(page)
        ]

    def effected_pages(self, file_path: Path):
        if not file_path in self:
            return []
        data_mod = self.get_data_mod_for(file_path)
        return [
            page for page in self.config.pages if data_mod.effects_template_file(page)
        ]

    def data_for(self, file_path: Path):
        """Get data for a specific template file path"""
        if not self.effects_template_file(file_path):
            return {}
        data = {**self.yaml_data, **self.global_data, **self.per_file_data(file_path)}
        for submod in self.submodules:
            data = {**data, **submod.data_for(file_path)}
        return data
