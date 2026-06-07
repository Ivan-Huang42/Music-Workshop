"""AI suggestion panel — melody continuation and chord recommendations."""

from __future__ import annotations

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from music_workshop.ai.client import DeepSeekClient, AISuggestion
from music_workshop.ai.melody import MelodyAssistant
from music_workshop.ai.harmony import HarmonyAssistant
from music_workshop.score.score_manager import ScoreManager


class AIPanelWidget(QWidget):
    """Side panel for AI-assisted composition suggestions.

    Provides buttons to request melody continuations and chord
    progressions, displays suggestions in a list, and lets the
    user accept/reject them.
    """

    def __init__(
        self,
        client: DeepSeekClient,
        score_manager: ScoreManager,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self._client = client
        self._score_manager = score_manager
        self._melody = MelodyAssistant(client, score_manager)
        self._harmony = HarmonyAssistant(client, score_manager)
        self._suggestions: list[AISuggestion] = []
        self._style = "classical"

        self._build_ui()

        # API status indicator
        if not client.is_enabled:
            self._status_label.setText("⚠️ No API key set")
            self._status_label.setStyleSheet("color: #c80; font-size: 11px;")
        else:
            self._status_label.setText("✓ DeepSeek ready")
            self._status_label.setStyleSheet("color: #080; font-size: 11px;")

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        # Title
        title = QLabel("AI Composer")
        title.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(title)

        # Status
        self._status_label = QLabel()
        layout.addWidget(self._status_label)

        # Style selector
        style_row = QHBoxLayout()
        style_row.addWidget(QLabel("Style:"))
        self._style_combo = QComboBox()
        self._style_combo.addItems(["classical", "pop", "jazz", "folk", "ambient"])
        self._style_combo.currentTextChanged.connect(self._on_style_changed)
        style_row.addWidget(self._style_combo)
        layout.addLayout(style_row)

        # --- Melody section ---
        layout.addWidget(self._make_separator())

        melody_label = QLabel("Melody")
        melody_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(melody_label)

        self._continue_btn = QPushButton("🎵 Suggest Continuation")
        self._continue_btn.clicked.connect(self._suggest_continuation)
        layout.addWidget(self._continue_btn)

        # --- Harmony section ---
        layout.addWidget(self._make_separator())

        harmony_label = QLabel("Harmony")
        harmony_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(harmony_label)

        self._chord_btn = QPushButton("🎸 Suggest Chords")
        self._chord_btn.clicked.connect(self._suggest_chords)
        layout.addWidget(self._chord_btn)

        # --- Suggestions list ---
        layout.addWidget(QLabel("Suggestions:"))
        self._suggestion_list = QListWidget()
        self._suggestion_list.setMinimumHeight(100)
        layout.addWidget(self._suggestion_list, stretch=1)

        # --- Action buttons ---
        action_row = QHBoxLayout()
        self._apply_btn = QPushButton("Apply")
        self._apply_btn.clicked.connect(self._apply_selected)
        self._apply_btn.setEnabled(False)
        action_row.addWidget(self._apply_btn)

        self._clear_btn = QPushButton("Clear AI")
        self._clear_btn.clicked.connect(self._clear_suggestions)
        action_row.addWidget(self._clear_btn)
        layout.addLayout(action_row)

        # Connect list selection
        self._suggestion_list.currentRowChanged.connect(self._on_selection_changed)

        # Loading indicator
        self._loading_label = QLabel("")
        self._loading_label.setAlignment(Qt.AlignCenter)
        self._loading_label.setStyleSheet("color: #888;")
        layout.addWidget(self._loading_label)

        layout.addStretch()

        self.setMinimumWidth(180)

    def _make_separator(self) -> QFrame:
        f = QFrame()
        f.setFrameShape(QFrame.HLine)
        f.setFrameShadow(QFrame.Sunken)
        return f

    def _on_style_changed(self, style: str) -> None:
        self._style = style

    # ------------------------------------------------------------------
    # AI actions
    # ------------------------------------------------------------------

    def _suggest_continuation(self) -> None:
        if self._score_manager.note_count == 0:
            self._set_loading("Record some notes first!", error=True)
            return
        self._set_loading("Thinking...")
        self._continue_btn.setEnabled(False)

        def do_work():
            self._suggestions = self._melody.suggest_continuation(
                num_notes=4, style=self._style
            )
            QTimer.singleShot(0, self._display_suggestions)
            self._continue_btn.setEnabled(True)
            self._set_loading("")

        QTimer.singleShot(10, do_work)

    def _suggest_chords(self) -> None:
        if self._score_manager.note_count == 0:
            self._set_loading("Record some notes first!", error=True)
            return
        self._set_loading("Thinking...")
        self._chord_btn.setEnabled(False)

        def do_work():
            self._suggestions = self._harmony.suggest_chords(style=self._style)
            QTimer.singleShot(0, self._display_suggestions)
            self._chord_btn.setEnabled(True)
            self._set_loading("")

        QTimer.singleShot(10, do_work)

    # ------------------------------------------------------------------
    # Display
    # ------------------------------------------------------------------

    def _display_suggestions(self) -> None:
        self._suggestion_list.clear()
        if not self._suggestions:
            self._suggestion_list.addItem("(no suggestions)")
            return
        for s in self._suggestions:
            item = QListWidgetItem(s.description)
            item.setData(Qt.UserRole, s)
            self._suggestion_list.addItem(item)

    def _clear_suggestions(self) -> None:
        self._suggestions.clear()
        self._suggestion_list.clear()
        self._apply_btn.setEnabled(False)

    # ------------------------------------------------------------------
    # Apply
    # ------------------------------------------------------------------

    def _on_selection_changed(self, row: int) -> None:
        self._apply_btn.setEnabled(row >= 0 and row < len(self._suggestions))

    def _apply_selected(self) -> None:
        row = self._suggestion_list.currentRow()
        if row < 0 or row >= len(self._suggestions):
            return
        suggestion = self._suggestions[row]
        # Determine if it's a melody or chord suggestion and apply
        if suggestion.data and "pitch" in suggestion.data:
            self._melody.apply_suggestion(suggestion)
        elif suggestion.data and "chord" in suggestion.data:
            self._harmony.apply_chord_as_notes(suggestion)
        self._clear_suggestions()
        # Emit signal to refresh notation (use parent or signal)
        parent = self.parent()
        if parent and hasattr(parent, "_on_note_recorded"):
            parent._on_note_recorded(0, 0)

    # ------------------------------------------------------------------
    # Loading indicator
    # ------------------------------------------------------------------

    def _set_loading(self, text: str, error: bool = False) -> None:
        self._loading_label.setText(text)
        if error:
            self._loading_label.setStyleSheet("color: #c00;")
        else:
            self._loading_label.setStyleSheet("color: #888;")
