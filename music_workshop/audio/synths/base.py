"""Abstract base class for all synthesizer algorithms."""

from abc import ABC, abstractmethod

import numpy as np


class BaseSynthesizer(ABC):
    """Abstract base for all synthesis algorithms.

    Subclasses generate audio samples for a single voice (monophonic).
    The caller manages note lifetime via repeated ``generate()`` calls
    and the returned phase value for glitch-free continuation.

    Args:
        sample_rate: Audio sample rate in Hz.
    """

    def __init__(self, sample_rate: int):
        self.sample_rate = sample_rate

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @abstractmethod
    def generate(
        self, note: int, velocity: float, num_samples: int, phase: float
    ) -> tuple[np.ndarray, float]:
        """Generate *num_samples* of audio for the given note.

        Args:
            note: MIDI note number (0-127). 69 = A4 = 440 Hz.
            velocity: Normalised note velocity (0.0-1.0).
            num_samples: Number of output samples to produce.
            phase: Phase scalar returned from the previous call (0 on first call).

        Returns:
            (buffer, new_phase)
            - buffer: 1-D float64 numpy array, length *num_samples*.
            - new_phase: Phase scalar to pass as *phase* on the next call.
        """

    @abstractmethod
    def reset(self) -> None:
        """Reset internal state for a fresh note onset."""

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def midi_to_freq(note: int) -> float:
        """Convert MIDI note number to frequency in Hz (A4 = 440 Hz)."""
        return 440.0 * (2.0 ** ((note - 69) / 12.0))
