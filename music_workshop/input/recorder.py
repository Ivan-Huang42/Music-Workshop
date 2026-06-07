"""Keyboard input recorder — captures note events and builds a score.

When recording is active, the Recorder tracks every key press/release
with millisecond timestamps, converts them to beat positions (based on
current BPM), quantises them to the user's chosen grid, and inserts
the resulting notes into a ScoreManager.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

from PySide6.QtCore import QObject, Signal

from music_workshop.input.quantizer import Quantizer, QuantizeResolution
from music_workshop.score.score_manager import ScoreManager


@dataclass
class NoteEvent:
    """Raw captured note event before quantisation."""

    note: int
    velocity: int
    start_timestamp_ms: int
    end_timestamp_ms: int | None = None


class Recorder(QObject):
    """Captures real-time keyboard events and writes them to a ScoreManager.

    Signals
    -------
    recording_started : emitted when recording begins.
    recording_stopped : emitted when recording ends (score is ready).
    note_recorded(midi_note, start_beat) : emitted for each committed note.
    """

    recording_started = Signal()
    recording_stopped = Signal()
    note_recorded = Signal(int, float)

    def __init__(
        self,
        score_manager: ScoreManager,
        quantizer: Quantizer,
        bpm: int = 120,
        parent: QObject | None = None,
    ):
        super().__init__(parent)
        self._score_manager = score_manager
        self._quantizer = quantizer
        self._bpm = bpm
        self._recording: bool = False
        self._active_notes: dict[int, NoteEvent] = {}
        self._recorded_events: list[NoteEvent] = []
        self._start_time_ms: int = 0

    # ------------------------------------------------------------------
    # Recording control
    # ------------------------------------------------------------------

    def start_recording(self) -> None:
        """Begin recording. Clears the score and starts fresh."""
        self._score_manager.clear()
        self._recording = True
        self._active_notes.clear()
        self._recorded_events.clear()
        self._start_time_ms = int(time.time() * 1000)
        self.recording_started.emit()

    def stop_recording(self) -> None:
        """Stop recording and commit any held notes."""
        if not self._recording:
            return
        # Release any still-pressed notes
        now = int(time.time() * 1000)
        for note in list(self._active_notes.keys()):
            self.on_key_release(note, now)
        self._recording = False
        self.recording_stopped.emit()

    @property
    def is_recording(self) -> bool:
        return self._recording

    # ------------------------------------------------------------------
    # Event capture (called from PianoWidget)
    # ------------------------------------------------------------------

    def on_key_press(self, note: int, velocity: int, timestamp_ms: int | None = None) -> None:
        """Record a note-on event."""
        if not self._recording:
            return
        ts = timestamp_ms or int(time.time() * 1000)
        # If this note somehow fired twice, release the first first
        if note in self._active_notes:
            self.on_key_release(note, ts)
        self._active_notes[note] = NoteEvent(
            note=note, velocity=velocity, start_timestamp_ms=ts
        )

    def on_key_release(self, note: int, timestamp_ms: int | None = None) -> None:
        """Record a note-off event: quantise and insert into score."""
        if not self._recording:
            return
        if note not in self._active_notes:
            return
        ts = timestamp_ms or int(time.time() * 1000)
        event = self._active_notes.pop(note)
        event.end_timestamp_ms = ts

        # Convert timestamps to quarter-note beat positions
        start_beat = self._ms_to_beats(event.start_timestamp_ms - self._start_time_ms)
        end_beat = self._ms_to_beats(ts - self._start_time_ms)

        # Apply quantisation
        q_start = self._quantizer.quantize_start(start_beat)
        q_dur = self._quantizer.quantize_duration(q_start, end_beat)

        # Guard: skip zero-length notes
        if q_dur < 0.01:
            return

        # Insert into the score
        self._score_manager.add_note(event.note, q_start, q_dur, event.velocity)
        self._recorded_events.append(event)
        self.note_recorded.emit(event.note, q_start)

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _ms_to_beats(self, ms: int) -> float:
        """Convert milliseconds to quarter-note beat position."""
        seconds = ms / 1000.0
        beat_duration = 60.0 / self._bpm
        return seconds / beat_duration

    def set_bpm(self, bpm: int) -> None:
        self._bpm = max(20, min(300, bpm))

    def get_recorded_events(self) -> list[NoteEvent]:
        return self._recorded_events.copy()
