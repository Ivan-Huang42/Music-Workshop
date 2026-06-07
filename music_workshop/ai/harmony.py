"""AI harmony assistant — chord suggestion and harmonisation."""

from __future__ import annotations

from music_workshop.ai.client import DeepSeekClient, AISuggestion
from music_workshop.score.score_manager import ScoreManager


class HarmonyAssistant:
    """AI-powered harmony assistant.

    Analyses the current melody and suggests chord progressions or
    harmonisation. Can also apply chords as chord notes in a
    secondary part (left hand).
    """

    def __init__(self, client: DeepSeekClient, score_manager: ScoreManager):
        self._client = client
        self._score = score_manager

    def suggest_chords(self, style: str = "classical") -> list[AISuggestion]:
        """Suggest chords for the current melody."""
        notes = self._extract_melody()
        return self._client.suggest_chords(notes, style)

    def apply_chord_as_notes(self, suggestion: AISuggestion) -> bool:
        """Apply a chord suggestion as notes in the 'chords' part.

        Parses the chord name (e.g. "C", "Dm", "G7") and inserts
        the constituent notes into a separate part.
        """
        if not suggestion.data:
            return False
        chord_str = suggestion.data.get("chord", "")
        start = float(suggestion.data.get("start_beat", 0))
        duration = float(suggestion.data.get("duration_beats", 4))

        pitches = self._chord_to_pitches(chord_str, octave=3)
        if not pitches:
            return False

        part = self._score.ensure_part("chords", "Left Hand")
        self._score.mark_snapshot()

        for p in pitches:
            n = __import__("music21").note.Note(p)
            n.quarterLength = duration
            n.volume.velocity = 70
            part.insert(start, n)

        print(f"[AI] Applied chord: {chord_str} at beat {start}")
        return True

    def _extract_melody(self, max_notes: int = 32) -> list[dict]:
        """Extract melody notes for analysis."""
        notes = []
        for el in self._score.active_part.recurse():
            if isinstance(el, __import__("music21").note.Note):
                notes.append({
                    "pitch": el.pitch.midi,
                    "dur": float(el.quarterLength),
                })
        return notes[-max_notes:]

    @staticmethod
    def _chord_to_pitches(chord_str: str, octave: int = 3) -> list[int]:
        """Convert a chord name to MIDI pitch list.

        Handles: C, Cm, D, Dm, E, Em, F, Fm, G, Gm, Am, Bm, G7, etc.
        """
        _NOTES = {"C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3,
                   "E": 4, "F": 5, "F#": 6, "Gb": 6, "G": 7, "G#": 8,
                   "Ab": 8, "A": 9, "A#": 10, "Bb": 10, "B": 11}

        # Parse root
        root_str = chord_str
        quality = "M"  # default major
        extra = ""

        if len(chord_str) >= 2 and chord_str[:2] in _NOTES:
            root_str = chord_str[:2]
            rest = chord_str[2:]
        elif chord_str[:1] in _NOTES:
            root_str = chord_str[:1]
            rest = chord_str[1:]
        else:
            return []

        # Determine quality
        if rest.startswith("m"):
            quality = "m"
            rest = rest[1:]
        elif rest.startswith("dim"):
            quality = "dim"
            rest = rest[3:]
        elif rest.startswith("aug"):
            quality = "aug"
            rest = rest[3:]

        extra = rest  # 7, maj7, etc.

        root = _NOTES.get(root_str)
        if root is None:
            return []

        base = 12 + octave * 12 + root

        if quality == "M":
            pitches = [base, base + 4, base + 7]
        elif quality == "m":
            pitches = [base, base + 3, base + 7]
        elif quality == "dim":
            pitches = [base, base + 3, base + 6]
        elif quality == "aug":
            pitches = [base, base + 4, base + 8]
        else:
            pitches = [base, base + 4, base + 7]

        # Add 7th if indicated
        if "7" in extra and "maj7" not in extra:
            if quality == "m":
                pitches.append(base + 10)  # minor 7th
            else:
                pitches.append(base + 10)  # dominant 7th
        elif "maj7" in extra:
            pitches.append(base + 11)

        return pitches
