import pytest
from conftest import BLOG_PATH, RESUME_PATH

from jinja2static import Config, build


@pytest.mark.parametrize(
    "test_type, project_file_path", [
        ("RESUME", RESUME_PATH), 
        ("BLOG", BLOG_PATH)]
)
def test_build_resume(test_type, project_file_path, logger):
    logger.warning(f"BUILDING {test_type} TEST")
    config = Config.from_(project_file_path)
    assert build(config)
