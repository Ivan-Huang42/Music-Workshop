"""Main application window — composes all panels and core services."""

from __future__ import annotations

import os

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QSplitter,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from music_workshop.ai.client import DeepSeekClient
from music_workshop.audio.engine import AudioEngine
from music_workshop.instruments.registry import InstrumentRegistry
from music_workshop.input.keyboard_mapper import KeyboardMapper
from music_workshop.input.quantizer import Quantizer, QuantizeResolution
from music_workshop.input.recorder import Recorder
from music_workshop.score.score_manager import ScoreManager
from music_workshop.ui.ai_panel import AIPanelWidget
from music_workshop.ui.instrument_panel import InstrumentPanelWidget
from music_workshop.ui.notation_view import NotationViewWidget
from music_workshop.ui.piano_widget import PianoWidget
from music_workshop.ui.transport_bar import TransportBarWidget
from music_workshop.ui.waveform_widget import WaveformWidget


class MainWindow(QMainWindow):
    """Top-level window composing all panels.

    Layout
    ------
    ::

        ┌──────────────────────────────────────┬──────────┬──────────┐
        │            Transport Bar             │          │          │
        ├──────────────────────────────────────┤          │          │
        │  [Notation] [Waveform] ← tab switch  │ Instrument│   AI     │
        │  ┌────────────────────────────────┐  │   Panel   │  Panel   │
        │  │  Notation or live waveform     │  │          │          │
        │  └────────────────────────────────┘  │          │          │
        ├──────────────────────────────────────┤          │          │
        │  [Part: Melody ▼]  Piano Keyboard   │          │          │
        └──────────────────────────────────────┴──────────┴──────────┘
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Music Workshop")
        self.resize(1400, 850)

        # ----------------------------------------------------------
        # Core services
        # ----------------------------------------------------------
        InstrumentRegistry.initialize()

        self._engine = AudioEngine()
        self._keyboard_mapper = KeyboardMapper()
        self._score_manager = ScoreManager()
        self._quantizer = Quantizer(QuantizeResolution.SIXTEENTH)
        self._recorder = Recorder(self._score_manager, self._quantizer)
        self._ai_client = DeepSeekClient()

        # ----------------------------------------------------------
        # UI components
        # ----------------------------------------------------------
        self._notation_view = NotationViewWidget()
        self._waveform_view = WaveformWidget(self._engine.mixer)
        self._piano_widget = PianoWidget(self._keyboard_mapper, self._engine)
        self._transport_bar = TransportBarWidget(
            engine=self._engine,
            recorder=self._recorder,
            quantizer=self._quantizer,
            notation_view=self._notation_view,
            score_manager=self._score_manager,
        )
        self._instrument_panel = InstrumentPanelWidget(self._engine)
        self._ai_panel = AIPanelWidget(self._ai_client, self._score_manager)

        # Part selector (right hand / left hand)
        self._part_selector = QComboBox()

        # ----------------------------------------------------------
        # Signal wiring
        # ----------------------------------------------------------
        self._recorder.note_recorded.connect(self._on_note_recorded)
        self._recorder.recording_stopped.connect(self._on_recording_stopped)
        self._piano_widget.set_recording_callback(self._on_key_event)

        # ----------------------------------------------------------
        # Layout
        # ----------------------------------------------------------
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.setSpacing(4)

        # Transport bar (top)
        main_layout.addWidget(self._transport_bar)

        # Main splitter: center area vs right panels
        h_splitter = QSplitter(Qt.Horizontal)

        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(4)

        # Tab widget: Notation | Waveform (top area)
        self._view_tabs = QTabWidget()
        self._view_tabs.addTab(self._notation_view, "🎼 Notation")
        self._view_tabs.addTab(self._waveform_view, "📊 Waveform")
        self._view_tabs.currentChanged.connect(self._on_tab_changed)
        left_layout.addWidget(self._view_tabs, stretch=3)

        # Part selector + piano keyboard strip
        piano_header = QHBoxLayout()
        piano_header.addWidget(QLabel("Part:"))
        piano_header.addWidget(self._part_selector)
        piano_header.addStretch()
        left_layout.addLayout(piano_header)

        # Piano keyboard (bottom)
        left_layout.addWidget(self._piano_widget, stretch=1)

        h_splitter.addWidget(left_panel)

        # Right panels: instrument + AI
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(4)

        # Setup parts
        self._score_manager.ensure_part("melody", "Right Hand")
        self._score_manager.ensure_part("chords", "Left Hand")
        self._part_selector.clear()
        self._part_selector.addItems(self._score_manager.part_names)

        right_layout.addWidget(self._instrument_panel)
        right_layout.addWidget(self._ai_panel, stretch=1)

        h_splitter.addWidget(right_panel)
        h_splitter.setStretchFactor(0, 3)
        h_splitter.setStretchFactor(1, 1)

        main_layout.addWidget(h_splitter)

        # ----------------------------------------------------------
        # Start audio engine
        # ----------------------------------------------------------
        self._engine.start()

    # ------------------------------------------------------------------
    # Signal handlers
    # ------------------------------------------------------------------

    def _on_tab_changed(self, index: int) -> None:
        """Toggle between Notation and Waveform views."""
        pass  # The tabs handle themselves

    def _on_part_changed(self, name: str) -> None:
        """Switch the active part for recording."""
        self._score_manager.active_part_name = name

    def _on_note_recorded(self, note: int, beat: float) -> None:
        """Refresh notation when a note is recorded."""
        # Switch to notation tab to show the result
        self._view_tabs.setCurrentIndex(0)
        score_json = self._score_manager.to_vexflow_json()
        self._notation_view.render_score(score_json)

    def _on_recording_stopped(self) -> None:
        """Refresh notation when recording stops."""
        self._view_tabs.setCurrentIndex(0)
        score_json = self._score_manager.to_vexflow_json()
        self._notation_view.render_score(score_json)

    def _on_key_event(
        self, note: int, velocity: int, timestamp_ms: int, is_press: bool
    ) -> None:
        """Bridge from PianoWidget key events to Recorder."""
        if is_press:
            self._recorder.on_key_press(note, velocity, timestamp_ms)
        else:
            self._recorder.on_key_release(note, timestamp_ms)
        self._transport_bar.update_octave_display(self._keyboard_mapper.octave_shift)

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def closeEvent(self, event):
        self._waveform_view.close()
        self._engine.stop()
        super().closeEvent(event)
