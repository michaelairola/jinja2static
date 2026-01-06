from __future__ import annotations

import logging
from typing import TYPE_CHECKING
import inspect
import importlib
import traceback
import sys
import yaml
from enum import Enum, auto
from dataclasses import dataclass, field

if TYPE_CHECKING:
    from pathlib import Path
    from .config import Config

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


def load_python_module(file_path: Path):
    module_name = str(file_path).replace("/", ".").removesuffix(".py")
    logger.debug(f"Getting module data from '{file_path}'")
    spec = importlib.util.spec_from_file_location(
        module_name, file_path
    )
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
    file_path = data_module.python_module_file_path
    if not file_path:
        return data_functions
    module = load_python_module(file_path)
    if not module:
        return data_functions
    all_functions = [
        f for (f_name, f) in inspect.getmembers(module, inspect.isfunction)
    ]
    for function in all_functions:
        func_type = getattr(function, "jinja2static", None)
        if not func_type:
            continue
        data_functions[func_type].append(function)
    return data_functions


@dataclass
class DataModule:
    config: Config = field()
    module_path: Path = field()

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
        with open(self.yaml_file_path, 'r') as stream:
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
            self.update_module_data()
        return self._global_data
    
    def update_module_data(self):
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


    def file_data(self, file_path: Path):
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
    def python_module_file_path(self):
        file_path_py = self.module_path.with_suffix(".py")
        if file_path_py.exists():
            return file_path_py
        if self.module_path.exists():
            return file_path
        logger.debug(f"No data module file found for '{self.module_path}'")
        return None 

    @property
    def yaml_file_path(self):
        file_path = self.module_path
        possible_yamls = [
            file_path.with_suffix(".yaml"),
            file_path.with_suffix(".yml"),
            file_path / "__init__.yaml",
            file_path / "__init__.yml",
        ]
        for file_path in possible_yamls:
            if file_path.exists():
                return file_path    
        logger.debug(f"No yaml file found for '{self.module_path}'")
        return None

    @property
    def relative_path(self):
        return self.module_path.relative_to(self.config.data)

    def contains(self, file_path: Path):
        return file_path.is_relative_to(self.relative_path)

    def data_for(self, file_path: Path):
        if not self.contains(file_path):
            return {}
        return {**self.yaml_data, **self.global_data, **self.file_data(file_path)}
