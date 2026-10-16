"""KDE Plasma Desktop Floating Overlay for PenguinOS Voice Assistant."""

import json
import os
import socket
import sys
import threading
from typing import Optional

from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt6.QtGui import QColor, QFont, QPainter, QPainterPath
from PyQt6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from daemon.ipc import get_socket_path


class IPCListener(QObject):
    """Listens for daemon events on a background thread and emits Qt signals."""
    event_received = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self._running = True

    def stop(self):
        self._running = False

    def listen(self):
        sock_path = get_socket_path()
        while self._running:
            if not os.path.exists(sock_path):
                import time
                time.sleep(1.0)
                continue

            try:
                client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                client.connect(sock_path)
                client.sendall(b'{"cmd":"subscribe"}\n')

                buf = ""
                while self._running:
                    chunk = client.recv(4096)
                    if not chunk:
                        break
                    buf += chunk.decode("utf-8", errors="ignore")
                    while "\n" in buf:
                        line, buf = buf.split("\n", 1)
                        line = line.strip()
                        if line:
                            try:
                                data = json.loads(line)
                                self.event_received.emit(data)
                            except Exception:
                                pass
                client.close()
            except Exception:
                import time
                time.sleep(1.0)


class AssistantOverlay(QWidget):
    """Floating pill HUD shown during voice assistant interactions."""

    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.hide_timer = QTimer(self)
        self.hide_timer.setSingleShot(True)
        self.hide_timer.timeout.connect(self.hide)

        self.init_ui()
        self.position_top_center()

    def init_ui(self):
        self.setStyleSheet("""
            QWidget#MainContainer {
                background-color: rgba(26, 30, 42, 235);
                border: 1px solid rgba(80, 150, 255, 0.4);
                border-radius: 20px;
            }
            QLabel {
                color: #FFFFFF;
                font-family: 'Segoe UI', 'Noto Sans', sans-serif;
            }
        """)

        container = QWidget(self)
        container.setObjectName("MainContainer")

        layout = QHBoxLayout(container)
        layout.setContentsMargins(18, 10, 20, 10)
        layout.setSpacing(12)

        # Status Dot / Icon Indicator
        self.status_dot = QLabel("●")
        self.status_dot.setStyleSheet("color: #38bdf8; font-size: 18px;")
        layout.addWidget(self.status_dot)

        # Text column
        v_layout = QVBoxLayout()
        v_layout.setSpacing(2)

        self.title_label = QLabel("Penguin Assistant")
        self.title_label.setFont(QFont("Noto Sans", 10, QFont.Weight.Bold))
        self.title_label.setStyleSheet("color: #38bdf8;")

        self.status_label = QLabel("Listening...")
        self.status_label.setFont(QFont("Noto Sans", 11))
        self.status_label.setWordWrap(True)

        v_layout.addWidget(self.title_label)
        v_layout.addWidget(self.status_label)
        layout.addLayout(v_layout)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(container)

        self.setFixedWidth(420)
        self.adjustSize()

    def position_top_center(self):
        screen = QApplication.primaryScreen()
        if screen:
            screen_geo = screen.availableGeometry()
            x = screen_geo.x() + (screen_geo.width() - self.width()) // 2
            y = screen_geo.y() + 45
            self.move(x, y)

    def handle_event(self, data: dict):
        event = data.get("event")
        if not event:
            return

        if event == "state_changed":
            state = data.get("state")
            if state == "listening":
                self.hide_timer.stop()
                self.status_dot.setStyleSheet("color: #38bdf8; font-size: 18px;")  # Sky Blue
                self.title_label.setText("Penguin Assistant")
                self.status_label.setText("Listening...")
                self.show()
                self.position_top_center()

            elif state == "processing":
                self.status_dot.setStyleSheet("color: #f59e0b; font-size: 18px;")  # Amber
                self.status_label.setText("Transcribing...")

            elif state == "executing":
                self.status_dot.setStyleSheet("color: #a855f7; font-size: 18px;")  # Purple

            elif state == "speaking":
                self.status_dot.setStyleSheet("color: #10b981; font-size: 18px;")  # Emerald Green

            elif state == "idle":
                # Auto-hide after 3.5 seconds
                self.hide_timer.start(3500)

        elif event == "transcript":
            text = data.get("text", "")
            if text:
                self.status_label.setText(f'"{text}"')
                self.adjustSize()
                self.position_top_center()

        elif event == "response":
            text = data.get("text", "")
            if text:
                self.status_label.setText(text)
                self.adjustSize()
                self.position_top_center()


def launch_overlay():
    app = QApplication(sys.argv)
    overlay = AssistantOverlay()

    listener = IPCListener()
    listener.event_received.connect(overlay.handle_event)

    t = threading.Thread(target=listener.listen, daemon=True)
    t.start()

    sys.exit(app.exec())


if __name__ == "__main__":
    launch_overlay()
