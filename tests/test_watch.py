import pytest
import sys
import subprocess
import time
import multiprocessing
from pathlib import Path

from jinja2static import Config
from jinja2static import watcher

from conftest import RESUME_PATH, BLOG_PATH

# PORT = 8006

def update_resume(config: Config) -> list[Path]:
    index_file = RESUME_PATH / config.templates / "index.html"
    index_file.touch(exist_ok=True)
    index_css = RESUME_PATH / config.assets / "index.css"
    index_css.touch(exist_ok=True)
    data_file = RESUME_PATH / "data.yaml"
    data_file.touch(exist_ok=True)
    return [index_file, index_css, data_file]

def update_blog(config: Config):
    index_file = BLOG_PATH / config.templates / "index.html"
    index_file.touch(exist_ok=True)
    index_css = BLOG_PATH / config.assets / "index.css"
    index_css.touch(exist_ok=True)
    data_file = BLOG_PATH / "data.py"
    data_file.touch(exist_ok=True)
    return [index_file, index_css, data_file]

@pytest.mark.parametrize("test_type, project_file_path, update_files_fn", [
    ( 'RESUME', RESUME_PATH, update_resume ),
    ( 'BLOG', BLOG_PATH, update_blog )
])
def test_run_dev_server_resume(test_type, project_file_path, update_files_fn, logger):
    logger.warning(f"DEV SERVER {test_type} TEST")
    config = Config.from_(project_file_path)
    run_cmd = [ sys.executable, "-m", "jinja2static", "watch" , str(project_file_path) ]
    process = subprocess.Popen(
        run_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    time.sleep(1)
    updated_files = update_files_fn(config)
    time.sleep(1)
    process.kill()
    stdout_data, stderr_data = process.communicate()
    stdout_str = stdout_data.decode('utf-8').strip()
    print(stdout_str)
    if stderr_data:
        assert False
    for file in updated_files:
        assert str(file) in stdout_str, f"No mention of '{str(file)}' found in stdout."

