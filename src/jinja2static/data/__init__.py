from __future__ import annotations

import logging
from typing import TYPE_CHECKING
import inspect
import importlib
import traceback
import sys
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


def get_callback_functions(data_module: DataModule):
    data_functions = {JinjaDataFunction.GLOBAL: [], JinjaDataFunction.PER_PAGE: []}
    try:
        if not data_module.module_path.exists():
            if data_module.module_path == data_module.config.data:
                logging.debug("No data detected. Building files without data...")
                return data_functions
            logger.warning(f"No module '{data_module.module_path}' found")
        module_name = str(data_module.module_path).replace("/", ".")
        logger.debug(f"Getting module '{module_name}' from '{data_module.module_path}'")
        spec = importlib.util.spec_from_file_location(
            module_name, data_module.module_path
        )
        if not spec or not spec.loader:
            logger.warning(f"Could not find module spec for '{module_name}'")
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        all_functions = [
            f for (f_name, f) in inspect.getmembers(module, inspect.isfunction)
        ]
    except Exception as e:
        logger.error(f"importing dynamic module '{module_name}': {e}")
        return data_functions
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
    # submodules: list[DataModule]

    # def __post_init__(self):
    #     pass
    _functions = {}

    @property
    def functions(self):
        if not self._functions:
            self._functions = get_callback_functions(self)
        return self._functions

    _global_data = {}

    @property
    def global_data(self):
        if not self._global_data:
            for f in self.functions[JinjaDataFunction.GLOBAL]:
                try:
                    self._global_data = {
                        **self._global_data,
                        **f(self._global_data, self.config),
                    }
                except Exception as e:
                    logger.error(f"{e}")
                    logger.info(traceback.format_exc())
        return self._global_data

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
    def relative_path(self):
        return self.module_path.relative_to(self.config.data)

    def contains(self, file_path: Path):
        return file_path.is_relative_to(self.relative_path)

    def data_for(self, file_path: Path):
        if not self.contains(file_path):
            return {}
        return {**self.global_data, **self.file_data(file_path)}
