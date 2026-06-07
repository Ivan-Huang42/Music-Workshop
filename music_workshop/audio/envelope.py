"""Four-stage ADSR envelope generator."""

import numpy as np


class ADSREnvelope:
    """Four-stage amplitude envelope (Attack-Decay-Sustain-Release).

    Generates a time-varying gain curve that shapes the amplitude of a sound
    over time. Stages proceed linearly: attack ramps up, decay drops to the
    sustain level, sustain holds until release is triggered, then release
    fades to silence.

    Args:
        attack: Time in seconds to ramp from 0 to peak (min 0.001s).
        decay: Time in seconds to fall from peak to sustain level.
        sustain_level: Level (0.0-1.0) held during sustain phase.
        release: Time in seconds to fade from sustain to 0 after release.
        sample_rate: Audio sample rate in Hz.
    """

    def __init__(
        self,
        attack: float = 0.01,
        decay: float = 0.1,
        sustain_level: float = 0.7,
        release: float = 0.3,
        sample_rate: int = 48000,
    ):
        self._sample_rate = sample_rate
        self._attack = max(attack, 0.001)
        self._decay = max(decay, 0.001)
        self._sustain_level = np.clip(sustain_level, 0.0, 1.0)
        self._release = max(release, 0.001)

        self._attack_samples = int(self._attack * sample_rate)
        self._decay_samples = int(self._decay * sample_rate)
        self._release_samples = int(self._release * sample_rate)

        self._state = "idle"  # idle | attack | decay | sustain | release | done
        self._idx = 0
        self._current_level = 0.0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def trigger(self) -> None:
        """Start the envelope from idle (begin attack phase)."""
        self._state = "attack"
        self._idx = 0
        self._current_level = 0.0

    def release(self) -> None:
        """Begin the release phase (if in attack/decay/sustain)."""
        if self._state in ("attack", "decay", "sustain"):
            self._state = "release"
            self._idx = 0

    def generate(self, num_samples: int) -> np.ndarray | None:
        """Generate *num_samples* of envelope gain values.

        Returns a float64 array of length *num_samples*, or ``None`` when
        the envelope has fully finished (all states exhausted).
        """
        if self._state == "idle":
            return np.zeros(num_samples, dtype=np.float64)

        out = np.empty(num_samples, dtype=np.float64)
        i = 0

        while i < num_samples and self._state != "done":
            if self._state == "attack":
                remaining = self._attack_samples - self._idx
                take = min(remaining, num_samples - i)
                for j in range(take):
                    val = (self._idx + j) / self._attack_samples
                    out[i + j] = val
                self._idx += take
                i += take
                self._current_level = 1.0
                if self._idx >= self._attack_samples:
                    self._state = "decay"
                    self._idx = 0

            elif self._state == "decay":
                remaining = self._decay_samples - self._idx
                take = min(remaining, num_samples - i)
                start_level = 1.0
                end_level = self._sustain_level
                for j in range(take):
                    frac = (self._idx + j) / self._decay_samples
                    out[i + j] = start_level + (end_level - start_level) * frac
                self._idx += take
                i += take
                self._current_level = end_level
                if self._idx >= self._decay_samples:
                    self._state = "sustain"
                    self._idx = 0

            elif self._state == "sustain":
                take = num_samples - i
                out[i : i + take] = self._sustain_level
                self._current_level = self._sustain_level
                i += take

            elif self._state == "release":
                rel_from = self._current_level
                remaining = self._release_samples - self._idx
                take = min(remaining, num_samples - i)
                for j in range(take):
                    frac = (self._idx + j) / self._release_samples
                    out[i + j] = rel_from * (1.0 - frac)
                self._idx += take
                i += take
                self._current_level = 0.0
                if self._idx >= self._release_samples:
                    self._state = "done"
                    if i < num_samples:
                        out[i:] = 0.0

        if self._state == "done":
            return out if i > 0 else None

        return out

    @property
    def finished(self) -> bool:
        """True if the envelope has completed its release phase."""
        return self._state == "done"

    @property
    def state(self) -> str:
        return self._state

    def reset(self) -> None:
        """Return to idle state."""
        self._state = "idle"
        self._idx = 0
        self._current_level = 0.0
