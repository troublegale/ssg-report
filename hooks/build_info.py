"""MkDocs-хук: метаданные сборки (коммит, ветка, время, площадка) в config.extra.build.

Значения выводятся в подвале каждой страницы и в <meta name="ssg-build-commit">,
по которому healthcheck в CI проверяет, что на хостинге лежит именно эта сборка.
"""

from __future__ import annotations

import os
import subprocess
from datetime import UTC, datetime
from typing import Any


def _git(*args: str) -> str:
    try:
        return subprocess.run(
            ["git", *args], capture_output=True, text=True, check=True
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return ""


def on_config(config: Any) -> Any:
    commit = os.environ.get("GITHUB_SHA") or _git("rev-parse", "HEAD") or "unknown"
    branch = (
        os.environ.get("GITHUB_HEAD_REF")
        or os.environ.get("GITHUB_REF_NAME")
        or _git("rev-parse", "--abbrev-ref", "HEAD")
        or "unknown"
    )
    config.extra["build"] = {
        "commit": commit,
        "commit_short": commit[:7],
        "branch": branch,
        "date": datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC"),
        "target": os.environ.get("DEPLOY_TARGET", "local"),
    }
    return config
