"""Instrument selection panel."""

from __future__ import annotations

from PySide6.QtWidgets import QComboBox, QLabel, QVBoxLayout, QWidget

from music_workshop.audio.engine import AudioEngine
from music_workshop.instruments.registry import InstrumentRegistry


class InstrumentPanelWidget(QWidget):
    """Side panel for selecting and controlling instruments.

    Currently provides a dropdown to switch between registered
    instrument presets. Will be extended in Phase 3 with per-instrument
    parameter editing.
    """

    def __init__(self, engine: AudioEngine, parent: QWidget | None = None):
        super().__init__(parent)
        self._engine = engine

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        # Title
        title = QLabel("Instrument")
        title.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(title)

        # Dropdown
        self._combo = QComboBox()
        self._combo.addItems(InstrumentRegistry.list_instruments())
        self._combo.currentTextChanged.connect(self._on_instrument_changed)
        layout.addWidget(self._combo)

        layout.addStretch()

        self.setMinimumWidth(150)

    def _on_instrument_changed(self, name: str) -> None:
        self._engine.set_instrument(name)

    @property
    def current_instrument(self) -> str:
        return self._combo.currentText()
