from pathlib import Path

import pytest

TASK_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def sources_dir() -> Path:
    return TASK_ROOT / "sources"
