"""Schroeder reverberator — classic algorithmic reverb."""

import numpy as np

from music_workshop.audio.effects.base import AudioEffect, CombFilter, AllPassFilter


class SchroederReverb(AudioEffect):
    """Schroeder reverberator: parallel comb filters → series all-pass filters.

    This is the classic digital reverb design (Schroeder, 1962). Four parallel
    comb filters create the initial echo density, followed by two all-pass
    filters in series to increase diffusion and smooth the colouration.

    Args:
        sample_rate: Audio sample rate in Hz.
        room_size: 0.0–1.0, scales delay times and feedback gains.
        damping: 0.0–1.0, high-frequency absorption (higher = warmer).
        mix: Dry/wet ratio (0.0 = dry, 1.0 = fully wet).
    """

    def __init__(
        self,
        sample_rate: int,
        room_size: float = 0.5,
        damping: float = 0.5,
        mix: float = 0.3,
    ):
        # Base delay times in seconds (staggered for density)
        base_delays = [0.030, 0.037, 0.041, 0.047]
        base_gains = [0.7, 0.65, 0.6, 0.55]

        # Scale by room size
        scale = 0.3 + 0.7 * room_size
        delays = [int(d * scale * sample_rate) for d in base_delays]
        # Ensure minimum delay of 2 samples
        delays = [max(d, 2) for d in delays]

        # Gain adjusted by damping: higher damping = lower feedback = less reverb
        damp_gain = 1.0 - damping * 0.3
        gains = [g * damp_gain for g in base_gains]

        self._combs = [
            CombFilter(delays[i], gains[i]) for i in range(4)
        ]

        # All-pass section (fixed, short delays)
        ap_delays = [int(0.005 * sample_rate), int(0.0017 * sample_rate)]
        ap_gains = [0.5, 0.5]
        self._allpasses = [
            AllPassFilter(ap_delays[0], ap_gains[0]),
            AllPassFilter(ap_delays[1], ap_gains[1]),
        ]

        self._mix = np.clip(mix, 0.0, 1.0)

    def process(self, signal: np.ndarray) -> np.ndarray:
        # Comb filter stage (parallel, summed)
        wet = np.zeros_like(signal)
        for comb in self._combs:
            wet += comb.process(signal)

        # Normalise comb sum
        wet /= len(self._combs)

        # All-pass stage (series)
        for ap in self._allpasses:
            wet = ap.process(wet)

        # Dry/wet mix
        return (1.0 - self._mix) * signal + self._mix * wet

    def reset(self) -> None:
        for c in self._combs:
            c.reset()
        for ap in self._allpasses:
            ap.reset()
