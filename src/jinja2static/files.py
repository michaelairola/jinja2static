import os
from pathlib import Path
import shutil
from functools import wraps
from asyncio import create_task, sleep
from datetime import datetime
import logging
import traceback

from jinja2 import Environment, FileSystemLoader, select_autoescape
from jinja2.exceptions import UndefinedError
from typing import TYPE_CHECKING

from .meta import dependency_graph
from .config import Config
from .data import data_functions

logger = logging.getLogger(__name__)


def rm_file_if_exists(file_path: Path):
    if file_path.exists():
        if file_path.is_dir():
            shutil.rmtree(file_path)
        else:
            os.remove(file_path)
