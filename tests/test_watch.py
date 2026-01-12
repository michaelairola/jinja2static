import os
from asyncio import create_task, sleep, wait_for
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest
from conftest import BLOG_PATH, RESUME_PATH
from watchfiles import Change, awatch

from jinja2static import Config, file_watcher


@dataclass
class ChangeAssertion:
    func: Any = field()
    src_file_path: Path = field()
    dst_file_changes: dict[Change, list[Path]] = field()

    def run(self, config: Config):
        return self.func(config, self.src_file_path)


modified_and_changed = [Change.modified, Change.added]


async def wait_for_file_change(file_path, expected_change):
    if not file_path.exists():
        if expected_change == Change.deleted:
            return
        if expected_change == Change.added:
            while True:
                if file_path.exists():
                    return
                await sleep(0.1)
    async for changes in awatch(file_path):
        for change, file_path in changes:
            if (
                change in modified_and_changed
                and expected_change in modified_and_changed
            ):
                return
            if change == expected_change:
                return


def touch(file_path: Path):
    return file_path.touch(exist_ok=True)


def touch_template_file(config: Config, file_path: Path):
    return touch(config.templates / file_path)


def touch_asset_file(config: Config, file_path: Path):
    return touch(config.assets / file_path)


def touch_data_file(config: Config, file_path: Path):
    return touch(config.project_path / file_path)


def delete_template_file(config: Config, file_path: Path):
    file_path = config.templates / file_path
    if file_path.exists():
        return os.remove(config.templates / file_path)


RESUME_CHANGES = [
    ChangeAssertion(
        touch_template_file, "index.html", {Change.modified: ["index.html"]}
    ),
    ChangeAssertion(touch_asset_file, "index.css", {Change.modified: ["index.css"]}),
    ChangeAssertion(touch_data_file, "data.yaml", {Change.modified: ["index.html"]}),
    # ChangeAssertion(touch_template_file, "RANDO_FILE.html", { Change.added: [ "RANDO_FILE.html" ]}),
    # ChangeAssertion(delete_template_file, "RANDO_FILE.html", { Change.deleted: [ ]}),
    # ChangeAssertion(delete_template_file, "RANDO_FILE.html", { Change.deleted: [ "RANDO_FILE.html" ]}),
]
BLOG_CHANGES = [
    ChangeAssertion(
        touch_template_file,
        "_base.html",
        {Change.modified: ["index.html", "about.html"]},
    ),
    ChangeAssertion(
        touch_data_file,
        "data/__init__.py",
        {Change.modified: ["index.html", "about.html", "posts/lorem_ipsum.html"]},
    ),
    ChangeAssertion(
        touch_data_file, "data/index.py", {Change.modified: ["index.html"]}
    ),
]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "test_type, project_file_path, project_changes",
    [
        ("RESUME", RESUME_PATH, RESUME_CHANGES),
        ("BLOG", BLOG_PATH, BLOG_CHANGES),
    ],
)
async def test_run_dev_server_resume(
    test_type, project_file_path, project_changes, logger
):
    config = Config.from_(project_file_path)
    logger.warning(f"DEV SERVER {test_type} TEST")

    create_task(file_watcher(config))

    for ca in project_changes:
        for change, file_paths in ca.dst_file_changes.items():
            for file_path in file_paths:
                task = create_task(
                    wait_for_file_change(config.dist / file_path, change)
                )
                await sleep(0.1)
                ca.run(config)
                try:
                    await wait_for(task, timeout=2)
                except TimeoutError:
                    assert False, (
                        f"file '{file_path}' did not get updated when {ca.func.__name__} was run on {ca.src_file_path} :("
                    )
                await sleep(0.1)
    await sleep(0.1)
