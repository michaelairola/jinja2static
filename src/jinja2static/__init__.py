import argparse
import logging
import shutil
import time
from asyncio import CancelledError, create_task, gather, run, sleep
from functools import wraps
from pathlib import Path

from .assets import copy_asset_dir
from .build import build
from .config import Config
from .init import initialize_project
from .logger import configure_logging
from .server import http_server
from .templates import build_pages
from .watcher import file_watcher

logger = logging.getLogger(__name__)


def allow_cancel(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except CancelledError:
            return

    return wrapper


@allow_cancel
async def initialize(config, args):
    initialize_project(args.project_file_path)


@allow_cancel
async def build_from_project_path(config: Config, _):
    return build(config)


@allow_cancel
async def run_watcher(config: Config, _):
    return await file_watcher(config)


@allow_cancel
async def run_http_server(config: Config, args):
    return await http_server(args.port, config)


@allow_cancel
async def run_dev_server(config: Config, args):
    build(config)
    task = create_task(http_server(args.port, config))
    await sleep(1)
    create_task(file_watcher(config))
    await gather(task)


PROJECT_PATH_ARG = (
    ["project_file_path"],
    {
        "help": "Specify project path or pyproject.toml file to run subcommand on.",
        "nargs": "?",
        "default": Path.cwd(),
        "type": Path,
    },
)

VERBOSE_ARG = (
    ["-v", "--verbose"],
    {
        "help": "Logs things verbosely.",
        "default": False,
        "action": "store_true",
    },
)

PORT_ARG = (
    ["-p", "--port"],
    {
        "help": "Port to run development server on.",
        "required": False,
        "default": 8000,
        "type": int,
    },
)

DEFAULT_ARGS = [PROJECT_PATH_ARG, VERBOSE_ARG]

MAIN_CLI = {
    "build": {
        "help": "Build a static site from a jinja2static project",
        "func": build_from_project_path,
    },
    "dev": {
        "help": "Run a development server that watches and recompiles src files.",
        "func": run_dev_server,
        "extra_args": [PORT_ARG],
    },
    "init": {
        "help": "initializes a project be configured as a jinja2static project.",
        "func": initialize,
    },
    "serve": {
        "help": "Serves the built files in the 'dist' directory.",
        "func": run_http_server,
        "extra_args": [PORT_ARG],
    },
    "watch": {
        "help": "Watches and recompiles src files (no server)",
        "func": run_watcher,
    },
}


def main():
    jinja2static = argparse.ArgumentParser(description="Jinja2Static")
    subcommands = jinja2static.add_subparsers(
        dest="command", help="Available subcommands"
    )
    for subcmd_name, subcmd_def in MAIN_CLI.items():
        help = subcmd_def.get("help", None)
        subcmd = subcommands.add_parser(
            subcmd_name,
            help=help,
        )
        func = subcmd_def.get("func", lambda _: print("Comming Soon!"))
        subcmd.set_defaults(func=func)
        EXTRA_ARGS = subcmd_def.get("extra_args", [])
        EXTRA_ARGS = [*DEFAULT_ARGS, *EXTRA_ARGS]
        for args, kwargs in EXTRA_ARGS:
            subcmd.add_argument(*args, **kwargs)

    cli_args = jinja2static.parse_args()
    configure_logging(cli_args.verbose)
    config = Config.from_(cli_args.project_file_path)
    if hasattr(cli_args, "func") and config:
        run(cli_args.func(config, cli_args))
    elif not config:
        return
    else:
        jinja2static.print_help()
