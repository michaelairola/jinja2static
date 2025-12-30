from __future__ import annotations

import logging
import importlib
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .config import Config

logger = logging.getLogger(__name__)

data_functions = []


def inject_data_function(func):
    data_functions.append(func)

    def wrapper(config):
        func(*args, **kwargs)

    return wrapper


def load_data_module(config: Config):
    if config.data.is_file():
        logger.debug(f"Importing data from '{config.data}'...")
        # TODO: make this a uuid?
        module_name = "jinja2static_data"
        # Create a module specification
        spec = importlib.util.spec_from_file_location(module_name, config.data)
        # Create a new module based on the spec
        module = importlib.util.module_from_spec(spec)
        # Register the module in sysmodule.modules (optional, but good practice)
        sys.modules[module_name] = module
        # Execute the module's code
        spec.loader.exec_module(module)
    else:
        logger.debug(f"No data file '{config.data}' found.")
