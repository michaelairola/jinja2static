from pathlib import Path

from jinja2static import Config
from jinja2static import build
from jinja2static.logger import configure_logging


def test_build_resume():
    RESUME_PATH = Path(__file__).parent / "data" / "resume"
    configure_logging(True)
    config = Config.from_(RESUME_PATH)
    assert build(config)


def test_build_blog():
    BLOG_PATH = Path(__file__).parent / "data" / "blog"
    configure_logging(True)
    config = Config.from_(BLOG_PATH)
    assert build(config)
