from pathlib import Path

from jinja2static.logger import configure_logging

from . import initialize_project

if __name__ == "__main__":
    configure_logging(True)
    initialize_project(Path.cwd())
