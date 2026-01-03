from pathlib import Path
from . import initialize_project
from jinja2static.logger import configure_logging

if __name__ == "__main__":
    configure_logging(True)
    initialize_project(Path.cwd())
