"""Visual piano keyboard widget with QWERTY key binding.

Draws a multi-octave piano keyboard and captures QKeyEvent to play
notes via the AudioEngine. Pressed keys are highlighted for visual
feedback.
"""

from __future__ import annotations

import time

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QKeyEvent, QPainter, QPen
from PySide6.QtWidgets import QWidget

from music_workshop.audio.engine import AudioEngine
from music_workshop.input.keyboard_mapper import KeyboardMapper


class PianoWidget(QWidget):
    """A visual piano keyboard playable via the computer keyboard.

    Draws 3 octaves of piano keys (C3–B5) with correct black/white key
    geometry. Highlights pressed keys in blue. Routes key events to the
    AudioEngine for sound and to an optional recording callback.

    Args:
        keyboard_mapper: Mapper for QWERTY → MIDI note conversion.
        engine: Audio engine to send note events to.
        parent: Parent Qt widget.
    """

    # MIDI note range to display (3 octaves)
    _START_NOTE = 48   # C3
    _END_NOTE = 83     # B5
    _WHITE_NOTES = [n for n in range(_START_NOTE, _END_NOTE + 1)
                    if n % 12 in (0, 2, 4, 5, 7, 9, 11)]

    # Black-key MIDI note → position index (which white key it sits between)
    _BLACK_POSITIONS: dict[int, int] = {}
    for n in range(_START_NOTE, _END_NOTE + 1):
        if n % 12 == 1:    # C#
            _BLACK_POSITIONS[n] = _WHITE_NOTES.index(n - 1)
        elif n % 12 == 3:  # D#
            _BLACK_POSITIONS[n] = _WHITE_NOTES.index(n - 1)
        elif n % 12 == 6:  # F#
            _BLACK_POSITIONS[n] = _WHITE_NOTES.index(n - 1)
        elif n % 12 == 8:  # G#
            _BLACK_POSITIONS[n] = _WHITE_NOTES.index(n - 1)
        elif n % 12 == 10:  # A#
            _BLACK_POSITIONS[n] = _WHITE_NOTES.index(n - 1)

    _NOTE_NAMES = ['C', '', 'D', '', 'E', 'F', '', 'G', '', 'A', '', 'B']

    def __init__(
        self,
        keyboard_mapper: KeyboardMapper,
        engine: AudioEngine,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self._mapper = keyboard_mapper
        self._engine = engine
        self._pressed_notes: set[int] = set()
        # Track which Qt key started which MIDI note, so release always
        # sends the correct note_off even if modifier state has changed.
        self._key_to_note: dict[int, int] = {}

        # Visual geometry (recalculated in paintEvent)
        self._white_key_count = len(self._WHITE_NOTES)
        self._white_key_width = 36.0
        self._black_key_width = 22.0
        self._key_height = 80.0

        self.setFocusPolicy(Qt.StrongFocus)
        self.setMinimumHeight(100)
        self.setMinimumWidth(400)

        # Optional: external note recording callback
        self._recording_callback = None

        # Timer to periodically check for key release glitches
        self._glitch_timer = QTimer(self)
        self._glitch_timer.setSingleShot(False)

    def set_recording_callback(self, callback) -> None:
        """Set a callable ``(note, velocity, timestamp_ms, is_press)``."""
        self._recording_callback = callback

    # ------------------------------------------------------------------
    # Qt event overrides
    # ------------------------------------------------------------------

    def keyPressEvent(self, event: QKeyEvent) -> None:
        key = event.key()
        modifiers = event.modifiers()

        note = self._mapper.key_to_note(key, modifiers)
        if note is None:
            super().keyPressEvent(event)
            return

        velocity = self._mapper.modifier_to_velocity(modifiers)

        # Start sound
        self._engine.note_on(note, velocity)
        self._pressed_notes.add(note)
        self._key_to_note[key] = note  # track for safe release

        # Notify recorder
        if self._recording_callback is not None:
            ts = int(time.time() * 1000)
            self._recording_callback(note, velocity, ts, True)

        self.update()

    def keyReleaseEvent(self, event: QKeyEvent) -> None:
        key = event.key()
        # Use stored mapping so we always send the right note_off,
        # even if modifier state has changed since the press.
        note = self._key_to_note.pop(key, None)
        if note is None:
            super().keyReleaseEvent(event)
            return

        # Stop sound
        self._engine.note_off(note)
        self._pressed_notes.discard(note)

        if self._recording_callback is not None:
            ts = int(time.time() * 1000)
            self._recording_callback(note, 0, ts, False)

        self.update()

    # ------------------------------------------------------------------
    # Painting
    # ------------------------------------------------------------------

    def paintEvent(self, event) -> None:  # noqa: ARG002
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()

        self._white_key_width = (w - 10) / self._white_key_count
        self._black_key_width = self._white_key_width * 0.6
        self._key_height = h - 8

        self._draw_white_keys(painter)
        self._draw_black_keys(painter)

    def _draw_white_keys(self, painter: QPainter) -> None:
        """Draw all white keys with labels."""
        for i, note in enumerate(self._WHITE_NOTES):
            x = 5 + i * self._white_key_width
            rect = (x, 4, self._white_key_width, self._key_height)

            # Colour: white normally, light blue when pressed
            if note in self._pressed_notes:
                painter.setBrush(QColor(180, 210, 255))
            else:
                painter.setBrush(QColor(255, 255, 255))
            painter.setPen(QPen(QColor(80, 80, 80), 1))
            painter.drawRect(*rect)

            # Note letter label
            label = self._NOTE_NAMES[note % 12]
            if label:
                painter.setPen(QColor(100, 100, 100))
                painter.drawText(
                    x + 4,
                    int(self._key_height - 8),
                    label,
                )

    def _draw_black_keys(self, painter: QPainter) -> None:
        """Draw black keys on top of the white keys."""
        for note, pos in self._BLACK_POSITIONS.items():
            x = 5 + pos * self._white_key_width - self._black_key_width / 2
            rect = (x, 4, self._black_key_width, self._key_height * 0.6)

            if note in self._pressed_notes:
                painter.setBrush(QColor(70, 90, 170))
            else:
                painter.setBrush(QColor(30, 30, 30))
            painter.setPen(QPen(QColor(0, 0, 0), 1))
            painter.drawRect(*rect)

    def sizeHint(self):
        return self.minimumSizeHint()
