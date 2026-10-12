"""Ensure one tray process per user."""

from __future__ import annotations

import getpass
import logging
from collections.abc import Callable

from PySide6.QtCore import QObject
from PySide6.QtNetwork import QLocalServer, QLocalSocket

_LOGGER = logging.getLogger(__name__)

_TOGGLE_MESSAGE = b"toggle\n"


def tray_instance_server_name(suffix: str | None = None) -> str:
    user = getpass.getuser()
    token = suffix if suffix is not None else "tray"
    safe_user = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in user)
    return f"cursor-usage-app-{token}-{safe_user}"


class SingleInstanceGuard(QObject):
    """
    Primary instance listens on a QLocalServer; secondary instances connect and delegate.

    Returns False from try_acquire when this process should exit (peer already running).
    """

    def __init__(
        self,
        server_name: str | None = None,
        on_peer_message: Callable[[bytes], None] | None = None,
    ) -> None:
        super().__init__()
        self._server_name = server_name or tray_instance_server_name()
        self._on_peer_message = on_peer_message
        self._server: QLocalServer | None = None

    @property
    def server_name(self) -> str:
        return self._server_name

    def try_acquire(self) -> bool:
        """True if this process is the primary instance."""
        if self._connect_and_delegate():
            return False

        QLocalServer.removeServer(self._server_name)
        server = QLocalServer(self)
        if not server.listen(self._server_name):
            if self._connect_and_delegate():
                return False
            _LOGGER.warning("Could not start single-instance server: %s", server.errorString())
            return True

        server.newConnection.connect(self._on_new_connection)
        self._server = server
        return True

    def release(self) -> None:
        if self._server is not None:
            self._server.close()
            QLocalServer.removeServer(self._server_name)
            self._server = None

    def _connect_and_delegate(self) -> bool:
        socket = QLocalSocket()
        socket.connectToServer(self._server_name)
        if not socket.waitForConnected(300):
            return False
        socket.write(_TOGGLE_MESSAGE)
        socket.flush()
        socket.waitForBytesWritten(300)
        socket.disconnectFromServer()
        return True

    def _on_new_connection(self) -> None:
        if self._server is None:
            return
        while self._server.hasPendingConnections():
            socket = self._server.nextPendingConnection()
            if socket is None:
                continue
            if socket.waitForReadyRead(300):
                payload = bytes(socket.readAll())
                if self._on_peer_message is not None and payload:
                    self._on_peer_message(payload)
            socket.disconnectFromServer()
