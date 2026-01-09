import os
import subprocess
import sys
import time
from pathlib import Path

import pytest
from conftest import BLOG_PATH, RESUME_PATH

from jinja2static import Config


def update_resume(config: Config) -> list[Path]:
    index_file = RESUME_PATH / config.templates / "index.html"
    index_file.touch(exist_ok=True)
    index_css = RESUME_PATH / config.assets / "index.css"
    index_css.touch(exist_ok=True)
    data_file = RESUME_PATH / "data.yaml"
    data_file.touch(exist_ok=True)
    rando_file = RESUME_PATH / config.templates / "RANDO_FILE.html"
    rando_file.touch()
    time.sleep(0.5)
    os.remove(rando_file)
    return [index_file, index_css, data_file, rando_file, rando_file]


def update_blog(config: Config):
    index_file = BLOG_PATH / config.templates / "index.html"
    index_file.touch(exist_ok=True)
    index_css = BLOG_PATH / config.assets / "index.css"
    index_css.touch(exist_ok=True)
    data_file = BLOG_PATH / "data.py"
    data_file.touch(exist_ok=True)
    return [index_file, index_css, data_file]


@pytest.mark.parametrize(
    "test_type, project_file_path, update_files_fn",
    [("RESUME", RESUME_PATH, update_resume), ("BLOG", BLOG_PATH, update_blog)],
)
def test_run_dev_server_resume(test_type, project_file_path, update_files_fn, logger):
    logger.warning(f"DEV SERVER {test_type} TEST")
    config = Config.from_(project_file_path)
    run_cmd = [sys.executable, "-m", "jinja2static", "watch", str(project_file_path)]
    process = subprocess.Popen(
        run_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    time.sleep(1)
    updated_files = update_files_fn(config)
    time.sleep(1.5)
    process.kill()
    stdout_data, stderr_data = process.communicate()
    stdout_str = stdout_data.decode("utf-8").strip()
    print(stdout_str)
    if stderr_data:
        print(stderr_data.decode("utf-8").strip())
        assert False

    for file in set(updated_files):
        cnt_expected = updated_files.count(file)
        cnt_actual = stdout_str.count(str(file))
        assert cnt_expected == cnt_actual, (
            f"No mention of '{str(file)}' found in stdout."
            if cnt_expected == 1 and cnt_actual == 0
            else f"'{str(file)}' expected {cnt_expected} times in stdout and {'only ' if cnt_actual else ''}showed {cnt_actual} time{'' if cnt_actual == 1 else 's'}"
        )
