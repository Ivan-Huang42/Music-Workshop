"""Sheet music display widget — renders VexFlow notation in a web view."""

from __future__ import annotations

import json
import os

from PySide6.QtCore import QUrl
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QVBoxLayout, QWidget


class NotationViewWidget(QWidget):
    """Displays sheet music using VexFlow inside a QWebEngineView.

    Receives score data as a JSON-serialisable dict and forwards it
    to the VexFlow JavaScript rendering page.
    """

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._webview = QWebEngineView()
        layout.addWidget(self._webview)

        # Load the VexFlow renderer HTML
        html_path = os.path.join(
            os.path.dirname(__file__), "..", "resources", "vexflow_renderer.html"
        )
        self._webview.setUrl(QUrl.fromLocalFile(os.path.abspath(html_path)))

    def render_score(self, vexflow_json: dict) -> None:
        """Send score data to the VexFlow page for rendering.

        Args:
            vexflow_json: Dict produced by ``ScoreManager.to_vexflow_json()``.
        """
        js = f"renderScore({json.dumps(vexflow_json)})"
        self._webview.page().runJavaScript(js)
