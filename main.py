#!/usr/bin/env python3
"""Music Workshop — AI-assisted music composition application.

Usage
-----
    python main.py
"""

import sys

from PySide6.QtWidgets import QApplication

from music_workshop.app import startup
from music_workshop.ui.main_window import MainWindow


def main() -> None:
    startup()

    app = QApplication(sys.argv)
    app.setApplicationName("Music Workshop")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
