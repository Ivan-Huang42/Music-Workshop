"""DeepSeek API client for AI-assisted composition.

Uses OpenAI-compatible Python SDK to call DeepSeek's chat API.
Supports melody continuation and harmony/chord suggestions.

Environment variable ``DEEPSEEK_API_KEY`` must be set, or you can
pass the key directly to ``DeepSeekClient``.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any

from openai import OpenAI


@dataclass
class AISuggestion:
    """A single suggestion from the AI model."""

    description: str
    data: dict[str, Any] | None = None


class DeepSeekClient:
    """Client for DeepSeek's chat API (OpenAI-compatible).

    Args:
        api_key: DeepSeek API key. Falls back to DEEPSEEK_API_KEY env var.
        model: Model name (default: ``deepseek-chat``).
        temperature: Sampling temperature (0.0–1.0).
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "deepseek-chat",
        temperature: float = 0.7,
    ):
        key = api_key or os.environ.get("DEEPSEEK_API_KEY", "")
        if not key:
            print("[AI] No DEEPSEEK_API_KEY set — AI features disabled")
        self._client = OpenAI(api_key=key, base_url="https://api.deepseek.com") if key else None
        self._model = model
        self._temperature = temperature
        self._enabled = bool(key)

    @property
    def is_enabled(self) -> bool:
        return self._enabled

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def suggest_melody_continuation(
        self,
        notes: list[dict[str, Any]],
        num_notes: int = 8,
        style: str = "classical",
    ) -> list[AISuggestion]:
        """Given existing notes, suggest a melody continuation.

        Args:
            notes: List of ``{"pitch": midi_int, "dur": quarter_beats}``.
            num_notes: How many notes to suggest.
            style: Musical style hint ("classical", "pop", "jazz", etc.).

        Returns:
            List of AISuggestion objects, each containing a proposed continuation.
        """
        if not self._enabled:
            return self._fallback_suggestions(notes, num_notes)

        prompt = self._build_continuation_prompt(notes, num_notes, style)
        response = self._call_api(prompt)
        return self._parse_continuation(response, num_notes)

    def suggest_chords(
        self,
        notes: list[dict[str, Any]],
        style: str = "classical",
    ) -> list[AISuggestion]:
        """Given a melody, suggest chord progressions.

        Args:
            notes: Melody notes, same format as above.
            style: Musical style hint.

        Returns:
            List of AISuggestion objects with chord data.
        """
        if not self._enabled:
            return self._fallback_chords(notes)

        prompt = self._build_chord_prompt(notes, style)
        response = self._call_api(prompt)
        return self._parse_chords(response)

    # ------------------------------------------------------------------
    # Prompt builders
    # ------------------------------------------------------------------

    def _build_continuation_prompt(
        self, notes: list[dict[str, Any]], num_notes: int, style: str
    ) -> str:
        note_str = ", ".join(
            f"{{pitch={n['pitch']}, dur={n['dur']:.2f}}}"
            for n in notes[-12:]  # last 12 notes for context
        )
        name = self._midi_notes_to_names(notes[-6:])

        return (
            f"You are a music composition assistant. Given these melody notes:\n"
            f"{note_str}\n"
            f"(Note names: {name})\n\n"
            f"Suggest a {num_notes}-note continuation in {style} style.\n"
            f"Respond ONLY with a JSON array: "
            f'[{{"pitch": 60, "dur": 1.0, "desc": "brief reason"}}, ...]\n'
            f"Pitch is MIDI note number (60=C4). Dur is quarter-note beats.\n"
            f"Keep it simple and musical."
        )

    def _build_chord_prompt(self, notes: list[dict[str, Any]], style: str) -> str:
        name = self._midi_notes_to_names(notes)
        return (
            f"You are a music harmony assistant. Given this melody:\n"
            f"{name}\n\n"
            f"Suggest a chord progression in {style} style.\n"
            f"Respond ONLY with a JSON array: "
            f'[{{"chord": "C", "start_beat": 0, "duration_beats": 4, "desc": "tonic"}}, ...]\n'
            f"Chord format: root note + type (C, Dm, Em, F, G7, Am, Bdim, etc.)."
        )

    # ------------------------------------------------------------------
    # API call
    # ------------------------------------------------------------------

    def _call_api(self, prompt: str) -> str:
        """Call DeepSeek API and return raw response text."""
        if not self._client:
            return "[]"
        try:
            resp = self._client.chat.completions.create(
                model=self._model,
                messages=[{"role": "user", "content": prompt}],
                temperature=self._temperature,
                max_tokens=1024,
            )
            return resp.choices[0].message.content or "[]"
        except Exception as e:
            print(f"[AI] API call failed: {e}")
            return "[]"

    # ------------------------------------------------------------------
    # Response parsers
    # ------------------------------------------------------------------

    def _parse_continuation(self, response: str, count: int) -> list[AISuggestion]:
        """Parse JSON response into AISuggestion list."""
        try:
            data = json.loads(self._extract_json(response))
            if not isinstance(data, list):
                return []
            return [
                AISuggestion(
                    description=f"{self._midi_note_name(n.get('pitch', 60))} "
                                f"({n.get('desc', '')})",
                    data=n,
                )
                for n in data[:count]
                if isinstance(n, dict) and "pitch" in n
            ]
        except (json.JSONDecodeError, TypeError):
            return []

    def _parse_chords(self, response: str) -> list[AISuggestion]:
        """Parse chord JSON into AISuggestion list."""
        try:
            data = json.loads(self._extract_json(response))
            if not isinstance(data, list):
                return []
            return [
                AISuggestion(
                    description=f"{c.get('chord', '?')} — {c.get('desc', '')}",
                    data=c,
                )
                for c in data
                if isinstance(c, dict) and "chord" in c
            ]
        except (json.JSONDecodeError, TypeError):
            return []

    # ------------------------------------------------------------------
    # Fallbacks (when API is not available)
    # ------------------------------------------------------------------

    def _fallback_suggestions(self, notes: list[dict], count: int) -> list[AISuggestion]:
        """Generate simple algorithmic continuations when API is unavailable."""
        if not notes:
            return [
                AISuggestion("C4 (tonic)", {"pitch": 60, "dur": 1.0, "desc": "tonic"}),
                AISuggestion("E4 (third)", {"pitch": 64, "dur": 0.5, "desc": "third"}),
                AISuggestion("G4 (fifth)", {"pitch": 67, "dur": 0.5, "desc": "fifth"}),
            ]

        last = notes[-1]
        base = last["pitch"]
        dur = max(last["dur"] * 0.5, 0.25)
        # Simple neighbor-tone continuation
        suggestions = [
            AISuggestion(f"{self._midi_note_name(base)} (repeat)", {"pitch": base, "dur": dur, "desc": "repeat"}),
            AISuggestion(f"{self._midi_note_name(base + 2)} (step up)", {"pitch": base + 2, "dur": dur, "desc": "step up"}),
            AISuggestion(f"{self._midi_note_name(base - 2)} (step down)", {"pitch": base - 2, "dur": dur, "desc": "step down"}),
        ]
        return suggestions[:count]

    def _fallback_chords(self, notes: list[dict]) -> list[AISuggestion]:
        """Simple chord suggestions when API is unavailable."""
        return [
            AISuggestion("C — tonic", {"chord": "C", "start_beat": 0, "duration_beats": 4, "desc": "tonic"}),
            AISuggestion("F — subdominant", {"chord": "F", "start_beat": 4, "duration_beats": 4, "desc": "subdominant"}),
            AISuggestion("G7 — dominant", {"chord": "G7", "start_beat": 8, "duration_beats": 4, "desc": "dominant"}),
            AISuggestion("C — tonic", {"chord": "C", "start_beat": 12, "duration_beats": 4, "desc": "resolution"}),
        ]

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_json(text: str) -> str:
        """Extract the first JSON array/object from text."""
        text = text.strip()
        start = text.find("[")
        if start == -1:
            start = text.find("{")
            end = text.rfind("}") + 1
        else:
            end = text.rfind("]") + 1
        if start >= 0 and end > start:
            return text[start:end]
        return "[]"

    @staticmethod
    def _midi_note_name(pitch: int) -> str:
        names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
        octave = (pitch // 12) - 1
        return f"{names[pitch % 12]}{octave}"

    @staticmethod
    def _midi_notes_to_names(notes: list[dict]) -> str:
        return " ".join(
            DeepSeekClient._midi_note_name(n["pitch"])
            for n in notes[-16:]
        )
