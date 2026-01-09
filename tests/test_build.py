import pytest

from jinja2static import build, Config

from conftest import RESUME_PATH, BLOG_PATH


@pytest.mark.parametrize("test_type, project_file_path", [
    ( 'RESUME', RESUME_PATH ),
    ( 'BLOG', BLOG_PATH )
])
def test_build_resume(test_type, project_file_path, logger):
    logger.warning(f"BUILDING {test_type} TEST")
    config = Config.from_(project_file_path)
    assert build(config)