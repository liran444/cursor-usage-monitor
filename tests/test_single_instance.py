import uuid

import pytest
from PySide6.QtWidgets import QApplication

from cursor_usage_app.app.single_instance import SingleInstanceGuard


@pytest.fixture
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


def test_single_instance_second_client_cannot_acquire(qapp) -> None:
    name = f"cursor-usage-test-{uuid.uuid4()}"
    primary = SingleInstanceGuard(server_name=name)
    assert primary.try_acquire() is True

    secondary = SingleInstanceGuard(server_name=name)
    assert secondary.try_acquire() is False

    primary.release()
