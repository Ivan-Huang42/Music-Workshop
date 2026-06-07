"""Additive synthesis — sum of harmonically-related sinusoids.

Additive synthesis reconstructs sounds by superimposing multiple sine
waves (partials) at harmonic or inharmonic frequency ratios, each with
its own amplitude envelope. This is the most direct application of
Fourier's theorem to sound synthesis.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from music_workshop.audio.synths.base import BaseSynthesizer


@dataclass
class Partial:
    """A single sinusoidal partial for additive synthesis.

    Attributes:
        harmonic: Frequency multiplier relative to the fundamental (1.0 = fund).
        amplitude: Relative onset amplitude (0.0–1.0).
        phase_offset: Initial phase offset in radians.
    """

    harmonic: float = 1.0
    amplitude: float = 0.5
    phase_offset: float = 0.0


class AdditiveSynthesizer(BaseSynthesizer):
    """Additive synthesis: sum of harmonically-related sinusoids.

    The classic organ drawbar model: each Partial is a sine wave at
    ``harmonic × fundamental_freq``, scaled by its amplitude. The result
    is a rich, harmonically complex tone.

    Args:
        sample_rate: Audio sample rate in Hz.
        partials: List of Partial dataclass instances.
    """

    def __init__(self, sample_rate: int, partials: list[Partial]):
        super().__init__(sample_rate)
        self._partials = partials

    def reset(self) -> None:
        pass  # Stateless — phase is caller-managed

    def generate(
        self, note: int, velocity: float, num_samples: int, phase: float
    ) -> tuple[np.ndarray, float]:
        freq = self.midi_to_freq(note)
        t = np.arange(num_samples, dtype=np.float64) / self.sample_rate
        out = np.zeros(num_samples, dtype=np.float64)

        for p in self._partials:
            partial_freq = freq * p.harmonic
            # Simple sine wave
            raw = np.sin(
                2.0 * np.pi * partial_freq * t + p.phase_offset
            )
            out += p.amplitude * raw

        # Normalise to prevent clipping
        peak = np.max(np.abs(out))
        if peak > 1.0:
            out /= peak

        return out * velocity, 0.0
