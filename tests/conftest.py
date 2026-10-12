from pathlib import Path

import pytest

from fixture_loader import FIXTURES_DIR


@pytest.fixture
def fixtures_dir() -> Path:
    return FIXTURES_DIR
