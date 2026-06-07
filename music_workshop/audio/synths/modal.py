"""Modal synthesis — resonant-mode percussion synthesis.

Modal synthesis models struck/percussive sounds by summing a set of
damped sinusoidal resonators (*modes*), each representing a natural
vibration mode of the physical object. The key to realism is using
*inharmonic* frequency ratios (e.g., 1:4:9.4:16.7 for marimba).
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from music_workshop.audio.synths.base import BaseSynthesizer


@dataclass
class Mode:
    """A single resonant mode in a modal synthesis model.

    Attributes:
        frequency_ratio: Frequency multiplier relative to fundamental.
        amplitude: Relative amplitude of this mode.
        decay_time: T60 decay time in seconds (time to -60 dB).
    """

    frequency_ratio: float = 1.0
    amplitude: float = 0.5
    decay_time: float = 1.0


class ModalSynthesizer(BaseSynthesizer):
    """Modal percussion synthesis with optional strike noise transient.

    Excites a bank of resonant modes with an impulse. Each mode rings
    at its frequency with exponential decay. A noise burst simulates the
    attack transient of a mallet or hammer strike.

    Args:
        sample_rate: Audio sample rate in Hz.
        modes: List of Mode dataclass instances.
        strike_noise: Amplitude of the initial noise burst (0.0–1.0).
        strike_decay: Decay time of the noise burst in seconds.
    """

    def __init__(
        self,
        sample_rate: int,
        modes: list[Mode],
        strike_noise: float = 0.3,
        strike_decay: float = 0.005,
    ):
        super().__init__(sample_rate)
        self._modes = modes
        self._strike_noise = strike_noise
        self._strike_decay = strike_decay
        self._elapsed_samples: int = 0

    def reset(self) -> None:
        self._elapsed_samples = 0

    def generate(
        self, note: int, velocity: float, num_samples: int, phase: float
    ) -> tuple[np.ndarray, float]:
        freq = self.midi_to_freq(note)
        t = np.arange(
            self._elapsed_samples,
            self._elapsed_samples + num_samples,
            dtype=np.float64,
        ) / self.sample_rate
        out = np.zeros(num_samples, dtype=np.float64)

        # Resonant modes: each is a sinusoid with exponential decay
        for mode in self._modes:
            mode_freq = freq * mode.frequency_ratio
            if mode.decay_time > 0:
                decay = np.exp(-np.log(1000.0) * t / mode.decay_time)
            else:
                decay = 1.0
            wave = np.sin(2.0 * np.pi * mode_freq * t)
            out += mode.amplitude * wave * decay

        # Strike transient (noise burst for mallet attack)
        if self._strike_noise > 0:
            noise = np.random.uniform(-1.0, 1.0, num_samples)
            noise_env = np.exp(-t / self._strike_decay)
            out += self._strike_noise * noise * noise_env

        self._elapsed_samples += num_samples

        # Normalise
        peak = np.max(np.abs(out))
        if peak > 1.0:
            out /= peak

        return out * velocity, 0.0
