"""Abstract base class for audio effects."""

from abc import ABC, abstractmethod

import numpy as np


class AudioEffect(ABC):
    """Base class for real-time audio effects (mono in, mono out)."""

    @abstractmethod
    def process(self, signal: np.ndarray) -> np.ndarray:
        """Process a mono audio block. Returns modified signal."""


class CombFilter:
    """Comb filter: y[n] = x[n] + gain * y[n - delay].

    Used as the building block for Schroeder reverberators.
    """

    def __init__(self, delay_samples: int, gain: float):
        self._buffer = np.zeros(delay_samples)
        self._idx = 0
        self._gain = gain

    def process(self, signal: np.ndarray) -> np.ndarray:
        out = np.empty_like(signal)
        for i in range(len(signal)):
            delayed = self._buffer[self._idx]
            out[i] = signal[i] + delayed * self._gain
            self._buffer[self._idx] = out[i]
            self._idx = (self._idx + 1) % len(self._buffer)
        return out

    def reset(self) -> None:
        self._buffer.fill(0.0)
        self._idx = 0


class AllPassFilter:
    """All-pass filter: y[n] = -gain*x[n] + x[n-delay] + gain*y[n-delay].

    Used in series after comb filters to increase echo density.
    """

    def __init__(self, delay_samples: int, gain: float):
        self._buffer = np.zeros(delay_samples)
        self._idx = 0
        self._gain = gain

    def process(self, signal: np.ndarray) -> np.ndarray:
        out = np.empty_like(signal)
        for i in range(len(signal)):
            delayed = self._buffer[self._idx]
            out[i] = -self._gain * signal[i] + delayed + self._gain * delayed
            self._buffer[self._idx] = signal[i] + self._gain * delayed
            self._idx = (self._idx + 1) % len(self._buffer)
        return out

    def reset(self) -> None:
        self._buffer.fill(0.0)
        self._idx = 0
