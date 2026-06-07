"""Chorus effect — thickens sound with modulated delayed copies."""

import numpy as np

from music_workshop.audio.effects.base import AudioEffect


class ChorusEffect(AudioEffect):
    """Chorus/flanger effect using modulated delay lines.

    Creates a thickening effect by mixing the dry signal with 2-3
    slightly detuned, modulated copies of itself.

    Args:
        sample_rate: Audio sample rate in Hz.
        voices: Number of detuned copies (1-3).
        rate: LFO rate in Hz (0.1–5.0).
        depth: Modulation depth in seconds (0.001–0.01).
        mix: Dry/wet ratio (0.0 = dry, 1.0 = full chorus).
    """

    def __init__(
        self,
        sample_rate: int,
        voices: int = 2,
        rate: float = 0.5,
        depth: float = 0.003,
        mix: float = 0.3,
    ):
        self._sample_rate = sample_rate
        self._voices = max(1, min(voices, 3))
        self._rate = rate
        self._depth = max(int(depth * sample_rate), 1)
        self._mix = np.clip(mix, 0.0, 1.0)

        # Per-voice LFO phase offsets (spread evenly)
        self._phases = [2.0 * np.pi * i / self._voices for i in range(self._voices)]
        # Per-voice gain tapering
        self._voice_gains = [1.0 / (self._voices + 1) for _ in range(self._voices)]

        # Fractional delay interpolation buffer (max 2x depth)
        max_delay = self._depth * 2 + 4
        self._buffer = np.zeros(max_delay + 1)
        self._write_idx = 0
        self._sample_count = 0

    def process(self, signal: np.ndarray) -> np.ndarray:
        out = np.zeros_like(signal)
        t = np.arange(self._sample_count,
                      self._sample_count + len(signal)) / self._sample_rate

        for v in range(self._voices):
            # LFO modulates delay length
            lfo = np.sin(2.0 * np.pi * self._rate * t + self._phases[v])
            # Delay offset: 0.5 + 0.5*sin → [0, 1] range, scaled by depth
            delay_offset = (lfo + 1.0) * 0.5 * self._depth
            delay_samples = delay_offset + 1.0  # minimum 1 sample

            wet = np.empty(len(signal), dtype=np.float64)
            for i in range(len(signal)):
                # Write current sample into buffer
                self._buffer[self._write_idx] = signal[i]
                # Read from delayed position with linear interpolation
                read_pos = self._write_idx - delay_samples[i]
                # Wrap around
                read_frac = read_pos - np.floor(read_pos)
                read_int = int(np.floor(read_pos)) % len(self._buffer)
                read_next = (read_int + 1) % len(self._buffer)
                # Linear interpolation
                delayed = (1.0 - read_frac) * self._buffer[read_int] + \
                          read_frac * self._buffer[read_next]
                wet[i] = delayed
                self._write_idx = (self._write_idx + 1) % len(self._buffer)

            out += wet * self._voice_gains[v]

        self._sample_count += len(signal)
        return (1.0 - self._mix) * signal + self._mix * out

    def reset(self) -> None:
        self._buffer.fill(0.0)
        self._write_idx = 0
        self._sample_count = 0
