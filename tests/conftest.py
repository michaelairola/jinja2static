import logging
from pathlib import Path

import pytest

from jinja2static import configure_logging

RESUME_PATH = Path(__file__).parent / "mock_repos" / "resume"
BLOG_PATH = Path(__file__).parent / "mock_repos" / "blog"


@pytest.fixture(scope="session")
def logger():
    configure_logging(False)
    logger = logging.getLogger(__name__)
    return logger
