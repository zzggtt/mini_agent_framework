"""Pytest bootstrap helpers for local package imports."""

from __future__ import annotations

import sys
from pathlib import Path


def _ensure_project_root_on_sys_path() -> None:
    """Adds the project root to sys.path so tests can import local packages."""

    project_root = Path(__file__).resolve().parent.parent
    project_root_str = str(project_root)
    if project_root_str not in sys.path:
        sys.path.insert(0, project_root_str)


_ensure_project_root_on_sys_path()
