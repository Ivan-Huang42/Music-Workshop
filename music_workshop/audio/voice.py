"""A single monophonic voice: one synthesizer + one envelope."""

import numpy as np

from music_workshop.audio.envelope import ADSREnvelope
from music_workshop.audio.synths.base import BaseSynthesizer
from music_workshop.instruments.registry import InstrumentRegistry, InstrumentDefinition


class Voice:
    """A single monophonic voice encapsulating a synthesizer and envelope.

    A voice is allocated by the Mixer when a note starts, drives its
    synthesizer and envelope in lockstep, and is recycled when the
    envelope finishes.

    Args:
        sample_rate: Audio sample rate in Hz.
    """

    def __init__(self, sample_rate: int):
        self._sample_rate = sample_rate
        self._synth: BaseSynthesizer | None = None
        self._envelope: ADSREnvelope | None = None
        self._active = False
        self._note: int = 0
        self._velocity: float = 0.0
        self._phase: float = 0.0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def trigger(self, note: int, velocity: float, defn: InstrumentDefinition) -> None:
        """Start this voice for *note* with the given instrument definition."""
        self._note = note
        self._velocity = velocity

        # Create a fresh synthesizer from the registry factory
        self._synth = InstrumentRegistry.create_synthesizer(
            defn.synth_type, defn.params, self._sample_rate
        )
        self._synth.reset()

        # Create the ADSR envelope from the instrument definition
        self._envelope = ADSREnvelope(
            attack=defn.envelope.get("attack", 0.01),
            decay=defn.envelope.get("decay", 0.1),
            sustain_level=defn.envelope.get("sustain_level", 0.7) * velocity,
            release=defn.envelope.get("release", 0.3),
            sample_rate=self._sample_rate,
        )
        self._envelope.trigger()
        self._active = True
        self._phase = 0.0

    def release(self) -> None:
        """Begin the release phase of the envelope."""
        if self._active and self._envelope is not None:
            self._envelope.release()

    def generate(self, num_samples: int) -> np.ndarray | None:
        """Generate *num_samples* of audio for this voice.

        Returns a float64 mono array, or ``None`` when the voice has
        finished (envelope completed).
        """
        if not self._active or self._envelope is None or self._synth is None:
            return None

        # Generate envelope
        env_block = self._envelope.generate(num_samples)
        if env_block is None:
            self._active = False
            return None

        # Generate synth audio
        synth_block, self._phase = self._synth.generate(
            self._note, self._velocity, num_samples, self._phase
        )

        # Apply envelope
        out = synth_block * env_block
        return out

    def reset(self) -> None:
        """Recycle this voice (return to the free pool)."""
        self._active = False
        self._synth = None
        self._envelope = None
        self._phase = 0.0

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def is_active(self) -> bool:
        return self._active

    @property
    def note(self) -> int:
        return self._note

    @property
    def finished(self) -> bool:
        return self._envelope is not None and self._envelope.finished
