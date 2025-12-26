from pathlib import Path
from dataclasses import dataclass, field
import logging
try:
    import tomllib
except ImportError:
    # Python < 3.11
    import tomli as tomllib

logger = logging.getLogger(__name__)

@dataclass 
class Config:
    templates: Path = field(default=Path("./templates"))
    static: Path = field(default=Path("./static"))
    dist: Path = field(default=Path("./dist"))
    pages: list[Path] = field(default_factory=lambda:["index.html"])

    @classmethod
    def from_(cls, file_path_str: str | None = None):
        logger.debug(f"Configuring project with '{file_path_str}'")
        file_path = Path(file_path_str) if file_path_str else Path.cwd()
        if not file_path.exists():
            logger.error(f"File Path '{file_path}' does not exist")
            return None
        if file_path.is_dir():
            logger.debug(f"Filepath '{file_path}' is a directory.")
            dir_path = file_path
            pyproject_path = file_path / "pyproject.toml"
        else:
            logger.debug(f"Filepath '{file_path}' is a configuration file.")
            dir_path = file_path.parent
            pyproject_path = file_path

        pyproject_data = {}
        try:
            with open(pyproject_path, "rb") as f:
                pyproject_data = tomllib.load(f)
        except FileNotFoundError:
            logger.debug(f"No pyproject.toml file found at {file_path}. Using default values.")
        except tomllib.TOMLDecodeError as e:
            logger.error(f"Unable to decoding TOML file: {e}")
            return None
        config_data = pyproject_data.get("tools", {}).get("jinja2static", {})
        dataclass_fields = [ k for k in cls.__dataclass_fields__.keys() ]
        config_data = {
            k: dir_path / Path(v) if isinstance(v, str) else v for k, v in config_data.items()
            if k in dataclass_fields
        }
        return cls(**config_data)

