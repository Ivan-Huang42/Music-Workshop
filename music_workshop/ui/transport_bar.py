"""Transport bar — recording, playback, export, and project controls."""

from __future__ import annotations

import os

from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QWidget,
)

from music_workshop.audio.engine import AudioEngine
from music_workshop.input.quantizer import Quantizer
from music_workshop.input.recorder import Recorder
from music_workshop.score.project import save_project, load_project
from music_workshop.score.score_manager import ScoreManager
from music_workshop.ui.notation_view import NotationViewWidget


class TransportBarWidget(QWidget):
    """Toolbar with recording, BPM, quantisation, export, and project controls.

    Layout
    ------
    [Record] [Play] [Stop] | BPM: [120] | Quantize: [16th] | Octave: +0
    [Undo] [Redo] | [Export MIDI] [Export XML] | [Save] [Load] [Clear]
    """

    def __init__(
        self,
        engine: AudioEngine,
        recorder: Recorder,
        quantizer: Quantizer,
        notation_view: NotationViewWidget,
        score_manager: ScoreManager,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self._engine = engine
        self._recorder = recorder
        self._quantizer = quantizer
        self._notation_view = notation_view
        self._score_manager = score_manager
        self._current_file: str | None = None

        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        # --- Row 1: Transport ---
        self._record_btn = QPushButton("● Record")
        self._record_btn.setCheckable(True)
        self._record_btn.clicked.connect(self._toggle_recording)
        self._record_btn.setStyleSheet(
            "QPushButton { padding: 4px 10px; }"
            "QPushButton:checked { background-color: #e33; color: white; font-weight: bold; }"
        )
        layout.addWidget(self._record_btn)

        self._play_btn = QPushButton("▶ Play")
        self._play_btn.clicked.connect(self._play)
        layout.addWidget(self._play_btn)

        self._stop_btn = QPushButton("■ Stop")
        self._stop_btn.clicked.connect(self._stop)
        layout.addWidget(self._stop_btn)

        layout.addSpacing(10)

        # BPM
        layout.addWidget(QLabel("BPM:"))
        self._bpm_spin = QSpinBox()
        self._bpm_spin.setRange(20, 300)
        self._bpm_spin.setValue(120)
        self._bpm_spin.valueChanged.connect(self._on_bpm_changed)
        layout.addWidget(self._bpm_spin)

        layout.addSpacing(6)

        # Quantize
        layout.addWidget(QLabel("Quantize:"))
        self._quant_combo = QComboBox()
        self._quant_combo.addItems(Quantizer.resolution_labels())
        self._quant_combo.setCurrentText("16th")
        self._quant_combo.currentTextChanged.connect(self._on_quant_changed)
        layout.addWidget(self._quant_combo)

        layout.addSpacing(10)

        # Octave
        self._octave_label = QLabel("Octave: 0")
        self._octave_label.setStyleSheet("color: #555; font-size: 12px;")
        layout.addWidget(self._octave_label)

        layout.addSpacing(10)

        # --- Undo / Redo ---
        self._undo_btn = QPushButton("↩ Undo")
        self._undo_btn.clicked.connect(self._undo)
        self._undo_btn.setEnabled(False)
        layout.addWidget(self._undo_btn)

        self._redo_btn = QPushButton("↪ Redo")
        self._redo_btn.clicked.connect(self._redo)
        self._redo_btn.setEnabled(False)
        layout.addWidget(self._redo_btn)

        layout.addSpacing(10)

        # --- Export ---
        self._export_midi_btn = QPushButton("🎵 MIDI")
        self._export_midi_btn.clicked.connect(self._export_midi)
        layout.addWidget(self._export_midi_btn)

        self._export_xml_btn = QPushButton("🎼 XML")
        self._export_xml_btn.clicked.connect(self._export_musicxml)
        layout.addWidget(self._export_xml_btn)

        layout.addSpacing(10)

        # --- Project ---
        self._save_btn = QPushButton("💾 Save")
        self._save_btn.clicked.connect(self._save_project)
        layout.addWidget(self._save_btn)

        self._load_btn = QPushButton("📂 Load")
        self._load_btn.clicked.connect(self._load_project)
        layout.addWidget(self._load_btn)

        layout.addSpacing(6)

        self._clear_btn = QPushButton("Clear")
        self._clear_btn.clicked.connect(self._clear_score)
        layout.addWidget(self._clear_btn)

        # Refresh undo/redo state periodically
        self._undo_timer = self.startTimer(500)

    # ------------------------------------------------------------------
    # Transport
    # ------------------------------------------------------------------

    def _toggle_recording(self, checked: bool) -> None:
        if checked:
            self._recorder.start_recording()
            self._record_btn.setText("● Recording...")
        else:
            self._recorder.stop_recording()
            self._record_btn.setText("● Record")
            self._refresh_notation()

    def _play(self) -> None:
        pass  # Future: score playback

    def _stop(self) -> None:
        self._engine.all_notes_off()
        if self._recorder.is_recording:
            self._record_btn.setChecked(False)
            self._toggle_recording(False)

    # ------------------------------------------------------------------
    # BPM / Quantize
    # ------------------------------------------------------------------

    def _on_bpm_changed(self, bpm: int) -> None:
        self._recorder.set_bpm(bpm)
        self._score_manager.bpm = bpm

    def _on_quant_changed(self, label: str) -> None:
        self._quantizer.set_resolution_from_label(label)

    # ------------------------------------------------------------------
    # Undo / Redo
    # ------------------------------------------------------------------

    def _refresh_notation(self) -> None:
        score_json = self._score_manager.to_vexflow_json()
        self._notation_view.render_score(score_json)

    def _undo(self) -> None:
        if self._score_manager.undo():
            self._refresh_notation()

    def _redo(self) -> None:
        if self._score_manager.redo():
            self._refresh_notation()

    def timerEvent(self, event) -> None:
        if event.timerId() == self._undo_timer:
            self._undo_btn.setEnabled(self._score_manager.can_undo)
            self._redo_btn.setEnabled(self._score_manager.can_redo)

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------

    def _export_midi(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Export MIDI", "", "MIDI files (*.mid)"
        )
        if path:
            self._score_manager.export_midi(path)

    def _export_musicxml(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Export MusicXML", "", "MusicXML files (*.xml *.mxl)"
        )
        if path:
            self._score_manager.export_musicxml(path)

    # ------------------------------------------------------------------
    # Project save/load
    # ------------------------------------------------------------------

    def _save_project(self) -> None:
        if self._current_file:
            path = self._current_file
        else:
            path, _ = QFileDialog.getSaveFileName(
                self, "Save Project", "", "Music Workshop Project (*.mwproj)"
            )
            if not path:
                return
        try:
            save_project(path, self._score_manager)
            self._current_file = path
        except Exception as e:
            print(f"Save failed: {e}")

    def _load_project(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Project", "", "Music Workshop Project (*.mwproj);;MIDI (*.mid)"
        )
        if not path:
            return

        if path.endswith(".mid"):
            from music_workshop.score.importer import import_midi_into_score
            import_midi_into_score(path, self._score_manager)
        else:
            load_project(path, self._score_manager)

        self._current_file = path
        self._refresh_notation()

    # ------------------------------------------------------------------
    # Clear
    # ------------------------------------------------------------------

    def _clear_score(self) -> None:
        self._score_manager.mark_snapshot()
        self._score_manager.clear()
        self._refresh_notation()

    # ------------------------------------------------------------------
    # Octave display
    # ------------------------------------------------------------------

    def update_octave_display(self, shift: int) -> None:
        self._octave_label.setText(f"Octave: {shift:+d}")
