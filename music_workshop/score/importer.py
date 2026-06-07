"""MIDI file import — reads standard MIDI files into ScoreManager."""

from __future__ import annotations

import music21 as m21


def import_midi(path: str) -> m21.stream.Score:
    """Load a MIDI file and return a music21 Score.

    Args:
        path: Path to a .mid file.

    Returns:
        A music21 Score object with Parts, Measures, and Notes.
    """
    return m21.converter.parse(path)


def import_midi_into_score(
    path: str,
    score_manager,
    part_index: int = 0,
) -> None:
    """Import a MIDI file's selected part into a ScoreManager.

    Args:
        path: Path to .mid file.
        score_manager: Target ScoreManager instance.
        part_index: Which MIDI track to import (0 = first).
    """
    score = import_midi(path)

    # Get all parts (tracks)
    parts = list(score.getElementsByClass(m21.stream.Part))
    if not parts:
        return

    if part_index >= len(parts):
        part_index = 0

    midi_part = parts[part_index]

    # Copy notes into the ScoreManager's part
    score_manager.clear()
    for el in midi_part.flatten().notesAndRests:
        if isinstance(el, m21.note.Note):
            score_manager.add_note(
                midi_pitch=el.pitch.midi,
                start_beat=float(el.offset),
                duration_beats=float(el.quarterLength),
                velocity=el.volume.velocity if el.volume else 100,
            )
        elif isinstance(el, m21.note.Rest):
            score_manager.add_rest(
                start_beat=float(el.offset),
                duration_beats=float(el.quarterLength),
            )

    # Copy tempo if present
    for el in midi_part.flatten().getElementsByClass(m21.tempo.MetronomeMark):
        score_manager.bpm = int(el.number)
        break
