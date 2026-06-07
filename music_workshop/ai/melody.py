"""AI melody assistant — continuation and generation."""

from __future__ import annotations

from music_workshop.ai.client import DeepSeekClient, AISuggestion
from music_workshop.score.score_manager import ScoreManager


class MelodyAssistant:
    """AI-powered melody assistant.

    Wraps DeepSeekClient with ScoreManager integration, so the AI can
    read the current composition and suggest continuations or variations.
    """

    def __init__(self, client: DeepSeekClient, score_manager: ScoreManager):
        self._client = client
        self._score = score_manager

    def suggest_continuation(self, num_notes: int = 4, style: str = "classical") -> list[AISuggestion]:
        """Suggest notes to continue the current melody."""
        notes = self._extract_recent_notes()
        return self._client.suggest_melody_continuation(notes, num_notes, style)

    def apply_suggestion(self, suggestion: AISuggestion) -> bool:
        """Insert a suggested note into the score.

        Returns True on success.
        """
        if not suggestion.data:
            return False
        pitch = suggestion.data.get("pitch")
        dur = suggestion.data.get("dur", 1.0)
        desc = suggestion.data.get("desc", "")
        if pitch is None:
            return False

        # Find the last note's end position
        last_end = self._find_last_end()
        self._score.mark_snapshot()
        self._score.add_note(pitch, last_end, dur, velocity=90)
        print(f"[AI] Applied: {self._client._midi_note_name(pitch)} ({desc})")
        return True

    def clear(self) -> None:
        """Remove AI-generated notes (notes past the original end)."""
        pass  # Let user undo manually

    def _extract_recent_notes(self, count: int = 16) -> list[dict]:
        """Get last N notes from the score as simple dicts."""
        notes = []
        for el in self._score.active_part.recurse():
            if isinstance(el, __import__("music21").note.Note):
                notes.append({
                    "pitch": el.pitch.midi,
                    "dur": float(el.quarterLength),
                })
        return notes[-count:]

    def _find_last_end(self) -> float:
        """Find the beat position where the last note ends."""
        last_end = 0.0
        for el in self._score.active_part.recurse():
            if isinstance(el, (__import__("music21").note.Note, __import__("music21").note.Rest)):
                end = float(el.offset) + float(el.quarterLength)
                if end > last_end:
                    last_end = end
        return last_end
