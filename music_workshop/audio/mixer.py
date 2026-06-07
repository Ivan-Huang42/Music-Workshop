"""Voice pool: mix active voices, apply effects chain and master volume."""

from __future__ import annotations

import numpy as np

from music_workshop.audio.effects.base import AudioEffect
from music_workshop.audio.voice import Voice
from music_workshop.instruments.registry import InstrumentRegistry


class Mixer:
    """Manages a pool of voices, sums them, applies effects, and master gain.

    The Mixer is the bridge between note events (from the engine) and
    the synthesizer voices. It handles voice allocation, stealing, and
    recycling so the audio callback only needs to call ``process()``.

    Args:
        sample_rate: Audio sample rate in Hz.
        max_voices: Maximum simultaneous voices (polyphony limit).
    """

    def __init__(self, sample_rate: int, max_voices: int = 32):
        self._sample_rate = sample_rate
        self._max_voices = max_voices
        self._voices: list[Voice] = []
        self._free_pool: list[Voice] = []
        self._master_volume: float = 0.8
        self._current_instrument: str = "acoustic_grand_piano"
        self._note_to_voices: dict[int, list[Voice]] = {}
        self._effects: list[AudioEffect] = []
        self._effects_dirty = True  # Rebuild effects on next process
        self._last_output: np.ndarray | None = None  # For waveform display

    # ------------------------------------------------------------------
    # Public API (called from engine event-drain)
    # ------------------------------------------------------------------

    def start_note(self, note: int, velocity: float) -> Voice | None:
        """Start a new voice for *note*."""
        defn = InstrumentRegistry.get(self._current_instrument)
        if defn is None:
            return None

        voice = self._acquire_voice()
        voice.trigger(note, velocity, defn)
        self._voices.append(voice)
        self._note_to_voices.setdefault(note, []).append(voice)
        return voice

    def release_note(self, note: int) -> None:
        """Release all voices playing *note*."""
        for voice in self._note_to_voices.get(note, []):
            voice.release()
        self._note_to_voices.pop(note, None)

    def all_notes_off(self) -> None:
        """Immediately release every active voice."""
        for voice in self._voices:
            voice.release()
        self._note_to_voices.clear()

    def process(self, num_samples: int) -> np.ndarray:
        """Generate a mixed mono block of *num_samples*.

        Iterates all active voices, sums their outputs, applies the
        instrument's effects chain, master volume, and hard clips.

        Returns a float32 array suitable for direct output.
        """
        if not self._voices:
            return np.zeros(num_samples, dtype=np.float32)

        # Rebuild effects chain if dirty
        if self._effects_dirty:
            self._rebuild_effects()
            self._effects_dirty = False

        # Sum voices into float64 for headroom
        mix = np.zeros(num_samples, dtype=np.float64)
        surviving: list[Voice] = []

        for voice in self._voices:
            block = voice.generate(num_samples)
            if block is not None:
                mix += block
                surviving.append(voice)
            else:
                self._recycle_voice(voice)

        self._voices = surviving
        self._prune_note_map()

        # Apply effects chain
        for effect in self._effects:
            mix = effect.process(mix)

        # Master volume and hard clip
        mix *= self._master_volume
        np.clip(mix, -1.0, 1.0, out=mix)

        self._last_output = mix.copy()
        return mix.astype(np.float32)

    def set_instrument(self, name: str) -> None:
        """Switch the current instrument preset."""
        if InstrumentRegistry.get(name) is not None:
            self._current_instrument = name
            self._effects_dirty = True  # Rebuild effects next process()

    @property
    def current_instrument(self) -> str:
        return self._current_instrument

    @property
    def active_voice_count(self) -> int:
        return len(self._voices)

    @property
    def last_output(self) -> np.ndarray | None:
        """Most recent audio block (for waveform display, read-only)."""
        return self._last_output

    # ------------------------------------------------------------------
    # Effects
    # ------------------------------------------------------------------

    def _rebuild_effects(self) -> None:
        """Build the effects chain from the current instrument definition."""
        self._effects.clear()
        defn = InstrumentRegistry.get(self._current_instrument)
        if defn is None:
            return

        for effect_desc in defn.effects_chain:
            effect = self._create_effect(effect_desc)
            if effect is not None:
                self._effects.append(effect)

    def _create_effect(self, desc: dict) -> AudioEffect | None:
        """Create an effect instance from a descriptor dict."""
        effect_type = desc.get("type", "")
        try:
            if effect_type == "reverb":
                from music_workshop.audio.effects.reverb import (  # noqa: PLC0415
                    SchroederReverb,
                )
                return SchroederReverb(
                    sample_rate=self._sample_rate,
                    room_size=desc.get("room_size", 0.5),
                    mix=desc.get("mix", 0.3),
                )
            if effect_type == "chorus":
                from music_workshop.audio.effects.chorus import (  # noqa: PLC0415
                    ChorusEffect,
                )
                return ChorusEffect(
                    sample_rate=self._sample_rate,
                    voices=desc.get("voices", 2),
                    rate=desc.get("rate", 0.5),
                    depth=desc.get("depth", 0.003),
                    mix=desc.get("mix", 0.3),
                )
        except Exception:
            pass
        return None

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _acquire_voice(self) -> Voice:
        """Get a voice from the free pool or steal the oldest one."""
        if self._free_pool:
            return self._free_pool.pop()

        if len(self._voices) >= self._max_voices:
            stolen = self._voices.pop(0)
            stolen.release()
            self._recycle_voice(stolen)
            return self._free_pool.pop()

        return Voice(self._sample_rate)

    def _recycle_voice(self, voice: Voice) -> None:
        voice.reset()
        self._free_pool.append(voice)

    def _prune_note_map(self) -> None:
        """Remove finished voices from the note-to-voice mapping."""
        for note in list(self._note_to_voices.keys()):
            self._note_to_voices[note] = [
                v for v in self._note_to_voices[note] if v.is_active
            ]
            if not self._note_to_voices[note]:
                del self._note_to_voices[note]
