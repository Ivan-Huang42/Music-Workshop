"""FM (Frequency Modulation) synthesis — DX7-style operator routing.

FM synthesis generates complex timbres by using one sine-wave oscillator
(the *modulator*) to modulate the frequency of another (the *carrier*).
Multiple operators can be arranged in series/parallel configurations
to produce a huge variety of instrument sounds.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

from music_workshop.audio.synths.base import BaseSynthesizer


@dataclass
class FMOperator:
    """One operator in an FM synthesis network.

    Each operator is a sine oscillator whose frequency is derived from
    the note pitch times a *freq_ratio*. The operator can optionally
    receive modulation from upstream operators and feed back into itself.
    """

    freq_ratio: float = 1.0
    amplitude: float = 0.5
    feedback: float = 0.0


class FMSynthesizer(BaseSynthesizer):
    """Frequency Modulation synthesis with configurable operator routing.

    Routing is specified as an adjacency list where each entry is
    ``(carrier_index, [modulator_indices, ...])``. The output of each
    modulator modulates the phase of its carrier.

    A simple 2-operator FM (operator 0 = carrier, operator 1 = modulator)::

        routing = [(0, [1])]   # operator 1 modulates operator 0

    A 3-operator cascade (operator 2 → operator 1 → operator 0)::

        routing = [(0, [1]), (1, [2])]

    Args:
        sample_rate: Audio sample rate in Hz.
        operators: List of FMOperator dataclass instances.
        routing: List of (carrier_idx, [modulator_idxs, ...]) tuples.
    """

    def __init__(
        self,
        sample_rate: int,
        operators: list[FMOperator],
        routing: list[tuple[int, list[int]]],
    ):
        super().__init__(sample_rate)
        self._operators = operators
        self._routing = routing
        self._phases: list[float] = [0.0] * len(operators)
        self._feedback_delays: list[float] = [0.0] * len(operators)

    def reset(self) -> None:
        self._phases = [0.0] * len(self._operators)
        self._feedback_delays = [0.0] * len(self._operators)

    def generate(
        self, note: int, velocity: float, num_samples: int, phase: float
    ) -> tuple[np.ndarray, float]:
        freq = self.midi_to_freq(note)
        t = np.arange(num_samples, dtype=np.float64) / self.sample_rate

        # Compute operator outputs bottom-up (modulators first)
        op_outputs: dict[int, np.ndarray] = {}
        final_out = np.zeros(num_samples, dtype=np.float64)

        for carrier_idx, mod_indices in self._routing:
            # Sum all modulator outputs for this carrier
            mod_sum = np.zeros(num_samples)
            for mod_idx in mod_indices:
                if mod_idx not in op_outputs:
                    op_outputs[mod_idx] = self._compute_operator(
                        mod_idx, freq, t, op_outputs
                    )
                mod_sum += op_outputs[mod_idx]

            # Compute carrier (with modulation)
            carrier_out = self._compute_operator(
                carrier_idx, freq, t, op_outputs, mod_sum
            )
            op_outputs[carrier_idx] = carrier_out
            final_out += carrier_out

        # Apply velocity scaling
        final_out *= velocity

        return final_out, 0.0

    def _compute_operator(
        self,
        idx: int,
        base_freq: float,
        t: np.ndarray,
        op_outputs: dict[int, np.ndarray],
        modulation: np.ndarray | None = None,
    ) -> np.ndarray:
        op = self._operators[idx]
        op_freq = base_freq * op.freq_ratio
        phase_increment = 2.0 * np.pi * op_freq

        # Accumulated phase + frequency modulation
        phase = self._phases[idx] + phase_increment * t

        if modulation is not None:
            phase += modulation

        # Feedback: previous output delayed into phase
        if op.feedback > 0.0 and self._feedback_delays[idx] != 0.0:
            phase += op.feedback * self._feedback_delays[idx]

        out = op.amplitude * np.sin(phase)

        # Store last value for optional feedback
        self._feedback_delays[idx] = out[-1]

        # Wrap phase for continuity
        self._phases[idx] = (self._phases[idx] + phase_increment * len(t)) % (2.0 * np.pi)

        return out
