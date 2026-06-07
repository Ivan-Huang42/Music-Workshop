"""Project save/load — serialises the entire composition to/from JSON.

The project file bundles the score (as MusicXML), instrument selection,
BPM, and metadata into a single .mwproj file (JSON format).
"""

from __future__ import annotations

import json
import os
import tempfile
import zipfile
from datetime import datetime
from typing import Any

from music_workshop.score.score_manager import ScoreManager


def save_project(path: str, score_manager: ScoreManager, metadata: dict | None = None) -> None:
    """Save a complete project to a .mwproj file.

    The file is a ZIP containing:
      - ``score.xml`` — MusicXML representation of the score
      - ``project.json`` — metadata, BPM, instrument, etc.

    Args:
        path: Output file path (should end in .mwproj).
        score_manager: The current ScoreManager instance.
        metadata: Optional dict with keys like "title", "author", etc.
    """
    meta: dict[str, Any] = {
        "version": "1.0",
        "created": datetime.now().isoformat(),
        "bpm": score_manager.bpm,
        "instrument": "",
        "title": "",
        "author": "",
    }
    if metadata:
        meta.update(metadata)

    # Export score to MusicXML in a temp buffer
    tmp_dir = tempfile.mkdtemp()
    try:
        xml_path = os.path.join(tmp_dir, "score.xml")
        score_manager.export_musicxml(xml_path)

        # Create ZIP
        with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.write(xml_path, "score.xml")
            zf.writestr("project.json", json.dumps(meta, indent=2))
    finally:
        import shutil

        shutil.rmtree(tmp_dir, ignore_errors=True)


def load_project(path: str, score_manager: ScoreManager) -> dict[str, Any]:
    """Load a .mwproj file into the given ScoreManager.

    Args:
        path: Path to .mwproj file.
        score_manager: Target ScoreManager to populate.

    Returns:
        The metadata dict from the project file.
    """
    import music21 as m21

    with zipfile.ZipFile(path, "r") as zf:
        # Read metadata
        meta = json.loads(zf.read("project.json"))

        # Read and parse MusicXML
        xml_data = zf.read("score.xml")
        tmp_dir = tempfile.mkdtemp()
        try:
            xml_path = os.path.join(tmp_dir, "score.xml")
            with open(xml_path, "wb") as f:
                f.write(xml_data)

            score = m21.converter.parse(xml_path)

            # Copy all parts into ScoreManager, preserving part structure
            score_manager.clear()
            part_idx = 0
            for part in score.getElementsByClass(m21.stream.Part):
                # Map part name: use MusicXML part name, or generate one
                pname = f"part_{part_idx}"
                if part.partName:
                    pname = part.partName.lower().replace(" ", "_")
                # Clean up name
                pname = "".join(c if c.isalnum() or c == "_" else "_" for c in pname)
                if not pname or pname[0].isdigit():
                    pname = f"part_{part_idx}"

                score_manager.ensure_part(pname, part.partName or "")
                part_idx += 1

                for el in part.flatten().notesAndRests:
                    if isinstance(el, m21.note.Note):
                        score_manager.add_note(
                            midi_pitch=el.pitch.midi,
                            start_beat=float(el.offset),
                            duration_beats=float(el.quarterLength),
                            velocity=el.volume.velocity if el.volume else 100,
                            part_name=pname,
                        )
                    elif isinstance(el, m21.note.Rest):
                        score_manager.add_rest(
                            start_beat=float(el.offset),
                            duration_beats=float(el.quarterLength),
                            part_name=pname,
                        )

            # Restore BPM
            score_manager.bpm = meta.get("bpm", 120)
        finally:
            import shutil

            shutil.rmtree(tmp_dir, ignore_errors=True)

    return meta
