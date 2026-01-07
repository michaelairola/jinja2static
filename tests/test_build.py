import subprocess
import sys
import time
from pathlib import Path
import logging

from jinja2static import configure_logging, build, Config

RESUME_PATH = Path(__file__).parent / "test_repos" / "resume"
BLOG_PATH = Path(__file__).parent / "test_repos" / "blog"

PORT = 8006
configure_logging(False)
logger = logging.getLogger(__name__)

def test_build_resume():
    logger.warning("BUILDING RESUME TEST")
    config = Config.from_(RESUME_PATH)
    assert build(config)


def test_build_blog():
    logger.warning("BUILDING BLOG TEST")
    config = Config.from_(BLOG_PATH)
    assert build(config)


def test_run_dev_server_resume():
    logger.warning("DEV SERVER RESUME TEST")
    config = Config.from_(RESUME_PATH)
    run_cmd = [ sys.executable, "-m", "jinja2static", "dev" , str(RESUME_PATH), "--port", str(PORT) ]
    process = subprocess.Popen(
        run_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    time.sleep(1)
    index_file = RESUME_PATH / config.templates / "index.html"
    index_file.touch(exist_ok=True)
    index_css = RESUME_PATH / config.assets / "index.css"
    index_css.touch(exist_ok=True)
    data_file = RESUME_PATH / "data.yaml"
    data_file.touch(exist_ok=True)
    time.sleep(1)
    process.kill()
    stdout_data, stderr_data = process.communicate()
    print(stdout_data.decode('utf-8'))
    if stderr_data:
        assert False


def test_run_dev_server_blog():
    logger.warning("DEV SERVER BLOG TEST")
    config = Config.from_(BLOG_PATH)
    run_cmd = [ sys.executable, "-m", "jinja2static", "dev" , str(BLOG_PATH), "--port", str(PORT) ]
    process = subprocess.Popen(
        run_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    time.sleep(1)
    index_file = BLOG_PATH / config.templates / "index.html"
    index_file.touch(exist_ok=True)
    index_css = BLOG_PATH / config.assets / "index.css"
    index_css.touch(exist_ok=True)
    data_file = BLOG_PATH / "data.py"
    data_file.touch(exist_ok=True)
    time.sleep(1)
    process.kill()
    stdout_data, stderr_data = process.communicate()
    print(stdout_data.decode('utf-8'))
    if stderr_data:
        assert False