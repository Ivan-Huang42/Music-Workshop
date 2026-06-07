"""Score export utilities — converts music21 data to display formats.

The primary export target is a JSON structure that VexFlow can render
as sheet music in the NotationView widget. MIDI, MusicXML, and LilyPond
exports are delegated to music21's built-in writers.
"""

from __future__ import annotations

import music21 as m21
from music21 import note as m21_note


def _duration_to_vex(quarter_length: float) -> tuple[str, int]:
    """Map a music21 quarterLength to a VexFlow duration string + dots.

    Returns (duration_str, dots_count).
    """
    mapping: dict[float, str] = {
        4.0: "w",  # whole
        2.0: "h",  # half
        1.0: "q",  # quarter
        0.5: "e",  # eighth
        0.25: "x",  # 16th
        0.125: "t",  # 32nd
    }
    dur = mapping.get(quarter_length)
    if dur is not None:
        return dur, 0

    # Try to detect dotted durations
    dotted_mapping: dict[float, str] = {
        3.0: "h",  # dotted half = half + dot
        1.5: "q",  # dotted quarter
        0.75: "e",  # dotted eighth
        0.375: "x",  # dotted 16th
    }
    dur = dotted_mapping.get(quarter_length)
    if dur is not None:
        return dur, 1

    # Fallback: snap to nearest standard duration
    import math

    log2 = math.log2(quarter_length)
    # Whole = 4 beats → 2^2, half = 2^1, quarter = 2^0, eighth = 2^-1, ...
    # log2(4.0)=2, log2(2.0)=1, log2(1.0)=0, log2(0.5)=-1
    nearest_pow = 2 ** round(log2)
    dots = 0
    # Check if a dotted version fits better
    for d in (1, 2):
        test_len = nearest_pow * (1 + (2**d - 1) / (2**d))
        if abs(quarter_length - test_len) < 0.05:
            dots = d
            break
    if dots == 0:
        dur = mapping.get(nearest_pow, "q")
    else:
        dur = mapping.get(nearest_pow * (1 + (dots - 1) / 2), "q")
    return dur, dots


def _note_to_vex(n: m21_note.Note) -> dict:
    """Convert a music21 Note to a VexFlow note dict."""
    pitch_str = f"{n.pitch.step}/{n.pitch.octave}"
    dur, dots = _duration_to_vex(n.quarterLength)
    acc = n.pitch.accidental
    result: dict = {
        "keys": [pitch_str],
        "duration": dur,
        "dots": dots,
    }
    if acc is not None and acc.name:
        result["accidentals"] = acc.name
    return result


def _rest_to_vex(r: m21_note.Rest) -> dict:
    """Convert a music21 Rest to a VexFlow rest dict."""
    dur, dots = _duration_to_vex(r.quarterLength)
    return {
        "keys": ["B/4"],
        "duration": dur,
        "dots": dots,
        "rest": True,
    }


def to_vexflow_json(part: m21.stream.Part, bpm: int = 120) -> dict:
    """Convert a music21 Part to a VexFlow-compatible JSON structure.

    Returns a dict with the following structure::

        {
            "bpm": int,
            "time_signature": str (e.g. "4/4"),
            "key_signature": "C" | "G" | ...,
            "measures": [ { "voices": [ { "notes": [ ... ] } ] } ]
        }

    Each note dict::

        {
            "keys": ["C/4"],
            "duration": "q" | "h" | ...,
            "dots": 0 | 1 | 2,
            "accidentals": "#" | "b" | None,
            "rest": True (if rest),
        }
    """
    # Use music21's makeNotation to properly beam and space notes
    try:
        m_stream = part.makeNotation(inPlace=False)
    except Exception:
        m_stream = part

    measures_list: list[dict] = []

    for m in m_stream.recurse().getElementsByClass("Measure"):
        vex_measure: dict = {"voices": [{"notes": []}]}
        for element in m.notesAndRests:
            if isinstance(element, m21_note.Note):
                vex_note = _note_to_vex(element)
            elif isinstance(element, m21_note.Rest):
                vex_note = _rest_to_vex(element)
            else:
                continue
            vex_measure["voices"][0]["notes"].append(vex_note)
        measures_list.append(vex_measure)

    # Extract time and key signatures from the flat stream
    ts = "4/4"
    ks = "C"
    for el in part.recurse():
        if isinstance(el, m21.meter.TimeSignature):
            ts = el.ratioString
        if isinstance(el, m21.key.KeySignature):
            ks = el.sharps

    return {
        "bpm": bpm,
        "time_signature": ts,
        "key_signature": ks,
        "measures": measures_list,
    }
