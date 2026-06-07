"""Music score manager — wraps music21 for score construction and export.

Supports multiple parts (right hand, left hand) and undo/redo history.
"""

from __future__ import annotations

import music21 as m21

from music_workshop.score.export import to_vexflow_json
from music_workshop.score.undo_manager import UndoManager


class ScoreManager:
    """Manages a music21 Score with multiple Parts and undo/redo.

    Args:
        time_signature: Default time signature string (e.g. "4/4").
        key: Default key signature.
    """

    def __init__(self, time_signature: str = "4/4", key: str = "C"):
        self._score = m21.stream.Score()
        self._time_signature = m21.meter.TimeSignature(time_signature)
        self._key_signature = m21.key.Key(key)
        self._bpm: int = 120

        # Parts dict
        self._parts: dict[str, m21.stream.Part] = {}
        self._add_part("melody", "Right Hand")
        self._active_part_name: str = "melody"

        # Note list for fast undo/redo: (pitch, offset, dur, vel, part)
        self._note_list: list[tuple[int, float, float, int, str]] = []

        # Undo/redo
        self._undo = UndoManager(max_history=50)
        self._snapshot_pending = False
        # Take initial snapshot
        self._undo.snapshot(self._note_list)

    # ------------------------------------------------------------------
    # Part management
    # ------------------------------------------------------------------

    def _add_part(self, name: str, long_name: str = "") -> m21.stream.Part:
        part = m21.stream.Part()
        part.partName = long_name or name
        part.append(self._time_signature)
        part.append(self._key_signature)
        self._parts[name] = part
        self._score.append(part)
        return part

    def ensure_part(self, name: str, long_name: str = "") -> m21.stream.Part:
        if name not in self._parts:
            self._add_part(name, long_name)
        return self._parts[name]

    @property
    def active_part_name(self) -> str:
        return self._active_part_name

    @active_part_name.setter
    def active_part_name(self, name: str) -> None:
        if name in self._parts:
            self._active_part_name = name

    @property
    def active_part(self) -> m21.stream.Part:
        return self._parts[self._active_part_name]

    @property
    def part_names(self) -> list[str]:
        return list(self._parts.keys())

    # ------------------------------------------------------------------
    # Note operations
    # ------------------------------------------------------------------

    def add_note(
        self,
        midi_pitch: int,
        start_beat: float,
        duration_beats: float,
        velocity: int = 100,
        part_name: str | None = None,
    ) -> None:
        """Insert a note in the specified or active part."""
        self._auto_snapshot()
        pn = part_name or self._active_part_name
        part = self._parts.get(pn)
        if part is None:
            return
        n = m21.note.Note(midi_pitch)
        n.quarterLength = duration_beats
        n.volume.velocity = velocity
        part.insert(start_beat, n)
        self._note_list.append((midi_pitch, start_beat, duration_beats, velocity, pn))

    def add_rest(self, start_beat: float, duration_beats: float, part_name: str | None = None) -> None:
        """Insert a rest in the specified or active part."""
        self._auto_snapshot()
        pn = part_name or self._active_part_name
        part = self._parts.get(pn)
        if part is None:
            return
        r = m21.note.Rest()
        r.quarterLength = duration_beats
        part.insert(start_beat, r)

    def remove_note(self, midi_pitch: int, start_beat: float, part_name: str | None = None) -> bool:
        """Remove the first matching note."""
        part = self._parts.get(part_name or self._active_part_name)
        if part is None:
            return False
        for el in list(part.iter()):
            if (
                isinstance(el, m21.note.Note)
                and el.pitch.midi == midi_pitch
                and abs(el.offset - start_beat) < 0.01
            ):
                self._auto_snapshot()
                part.remove(el)
                # Remove from note list
                self._note_list = [
                    t for t in self._note_list
                    if not (t[0] == midi_pitch and abs(t[1] - start_beat) < 0.01)
                ]
                return True
        return False

    def clear(self, part_name: str | None = None) -> None:
        """Clear notes/rests from specified part (or all if None)."""
        self._auto_snapshot()
        to_clear = [part_name] if part_name else list(self._parts.keys())
        for pn in to_clear:
            part = self._parts.get(pn)
            if part is None:
                continue
            to_remove = [
                el for el in part
                if isinstance(el, (m21.note.Note, m21.note.Rest))
            ]
            for el in to_remove:
                part.remove(el)

        if part_name is None:
            self._note_list.clear()
        else:
            self._note_list = [t for t in self._note_list if t[4] != part_name]

    # ------------------------------------------------------------------
    # Undo/redo
    # ------------------------------------------------------------------

    def _auto_snapshot(self) -> None:
        """Take a snapshot before a mutation if one is pending."""
        if self._snapshot_pending:
            self._undo.snapshot(list(self._note_list))
            self._snapshot_pending = False

    def _rebuild_from_notes(self, notes: list[tuple]) -> None:
        """Rebuild all parts from a list of note tuples."""
        # Clear all parts
        for part in self._parts.values():
            to_remove = [
                el for el in part
                if isinstance(el, (m21.note.Note, m21.note.Rest))
            ]
            for el in to_remove:
                part.remove(el)

        # Re-insert notes
        self._note_list = list(notes)
        for pitch, offset, dur, vel, pn in notes:
            part = self._parts.get(pn)
            if part is None:
                continue
            n = m21.note.Note(pitch)
            n.quarterLength = dur
            n.volume.velocity = vel
            part.insert(offset, n)

    def mark_snapshot(self) -> None:
        """Mark that the next mutation should trigger a snapshot."""
        self._snapshot_pending = True

    def undo(self) -> bool:
        """Undo the last mutation."""
        self._snapshot_pending = False
        result = self._undo.undo(list(self._note_list))
        if result is not None:
            self._rebuild_from_notes(result)
            return True
        return False

    def redo(self) -> bool:
        """Redo the last undone mutation."""
        self._snapshot_pending = False
        result = self._undo.redo(list(self._note_list))
        if result is not None:
            self._rebuild_from_notes(result)
            return True
        return False

    @property
    def can_undo(self) -> bool:
        return self._undo.can_undo

    @property
    def can_redo(self) -> bool:
        return self._undo.can_redo

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------

    @property
    def note_count(self) -> int:
        return len(self._note_list)

    @property
    def bpm(self) -> int:
        return self._bpm

    @bpm.setter
    def bpm(self, value: int) -> None:
        self._bpm = max(20, min(300, value))

    @property
    def score(self) -> m21.stream.Score:
        return self._score

    @property
    def part(self) -> m21.stream.Part:
        return self.active_part

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------

    def to_vexflow_json(self, part_name: str | None = None) -> dict:
        """Serialize score to VexFlow JSON."""
        if part_name:
            part = self._parts.get(part_name)
            if part is None:
                return {"bpm": self._bpm, "time_signature": "4/4", "key_signature": "C", "measures": []}
            return to_vexflow_json(part, self._bpm)

        # Merge all parts
        from music21 import stream as m21_stream
        merged = m21_stream.Part()
        for p in self._parts.values():
            for el in p.recurse().notesAndRests:
                merged.insert(float(el.offset), el)
        return to_vexflow_json(merged, self._bpm)

    def export_midi(self, path: str) -> None:
        """Write a standard MIDI file."""
        from music21 import tempo as m21_tempo
        for part in self._parts.values():
            part.insert(0.0, m21_tempo.MetronomeMark(number=self._bpm))
        mfp = m21.midi.translate.streamToMidiFile(self._score)
        mfp.open(path, "wb")
        mfp.write()
        mfp.close()
        for part in self._parts.values():
            for el in list(part.getElementsByClass(m21.tempo.MetronomeMark)):
                part.remove(el)

    def export_musicxml(self, path: str) -> None:
        self._score.write("musicxml", fp=path)

    def export_lilypond(self, path: str) -> None:
        self._score.write("lilypond", fp=path)
