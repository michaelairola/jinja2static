import argparse
from pathlib import Path
from asyncio import run
import logging

from .files import build
from .config import Config
from .server import server
from .logger import configure_logging

logger = logging.getLogger(__name__)

def build_from_project_path(args):
    configure_logging(args.verbose)
    config = Config.from_(args.project_file_path)
    return build(config)

def run_dev_server(args):
    configure_logging(args.verbose)
    config = Config.from_(args.project_file_path)
    build(config)
    run(server(args.port, config))

def initialize(args):
    configure_logging(args.verbose)
    logger.warning("Sorry, this has not been created yet.")


def main():
    jinja2static = argparse.ArgumentParser(description="Jinja2Static")
    subcommands = jinja2static.add_subparsers(dest='command', help='Available subcommands')

    build = subcommands.add_parser(
        'build', 
        help='Build a static site from a jinja2static project',
    )
    build.set_defaults(func=build_from_project_path)
    
    dev_server = subcommands.add_parser(
        'dev', 
        help='Run a development server that watches and recompiles src files.',
    )
    dev_server.add_argument("-p", "--port", default=8000, required=False, help="Port to run development server on.")
    dev_server.set_defaults(func=run_dev_server)
    
    init = subcommands.add_parser(
        "init",
        help="initializes a project be configured as a jinja2static project."
    )
    init.set_defaults(func=initialize)

    for parser in [ build, dev_server, init ]:
        parser.add_argument("-v", "--verbose", action="store_true", default=False, help="Logs things verbosely.")
        parser.add_argument(
            "project_file_path", 
            nargs='?', default=Path.cwd(), type=Path,
            help="Specify project path or pyproject.toml file to run subcommand on."
        )
    args = jinja2static.parse_args()
    if hasattr(args, 'func'):
        args.func(args)
    else:
        jinja2static.print_help()
