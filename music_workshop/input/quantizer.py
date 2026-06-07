"""Note timing quantizer — snaps raw timestamps to a musical grid.

The quantizer allows the user to adjust the "resolution" of keyboard
input, making it easier to produce clean notation even with imprecise
timing. Lower resolution (whole/half notes) is more forgiving; higher
resolution (16th/32nd) captures more detail.
"""

from __future__ import annotations

from enum import Enum


class QuantizeResolution(Enum):
    """Musical note lengths available for quantization."""

    WHOLE = "whole"
    HALF = "half"
    QUARTER = "quarter"
    EIGHTH = "eighth"
    SIXTEENTH = "16th"
    THIRTYSECOND = "32nd"

    def beat_value(self) -> float:
        """Return the duration in quarter-note beats."""
        return {
            QuantizeResolution.WHOLE: 4.0,
            QuantizeResolution.HALF: 2.0,
            QuantizeResolution.QUARTER: 1.0,
            QuantizeResolution.EIGHTH: 0.5,
            QuantizeResolution.SIXTEENTH: 0.25,
            QuantizeResolution.THIRTYSECOND: 0.125,
        }[self]


_RESOLUTION_FROM_LABEL: dict[str, QuantizeResolution] = {
    "whole": QuantizeResolution.WHOLE,
    "half": QuantizeResolution.HALF,
    "quarter": QuantizeResolution.QUARTER,
    "eighth": QuantizeResolution.EIGHTH,
    "16th": QuantizeResolution.SIXTEENTH,
    "32nd": QuantizeResolution.THIRTYSECOND,
}


class Quantizer:
    """Snaps note start times and durations to a user-selectable grid.

    Args:
        resolution: Initial quantization resolution.
    """

    def __init__(self, resolution: QuantizeResolution = QuantizeResolution.SIXTEENTH):
        self._resolution = resolution

    # ------------------------------------------------------------------
    # Resolution
    # ------------------------------------------------------------------

    @property
    def resolution(self) -> QuantizeResolution:
        return self._resolution

    @resolution.setter
    def resolution(self, res: QuantizeResolution) -> None:
        self._resolution = res

    def set_resolution_from_label(self, label: str) -> None:
        """Set resolution by display name (e.g. ``"16th"``)."""
        parsed = _RESOLUTION_FROM_LABEL.get(label.lower())
        if parsed is not None:
            self._resolution = parsed

    # ------------------------------------------------------------------
    # Quantization
    # ------------------------------------------------------------------

    def quantize_start(self, beat: float) -> float:
        """Snap a beat position to the nearest grid point.

        Args:
            beat: Raw beat position (e.g., 3.7 quarters from start).

        Returns:
            Snapped beat position.
        """
        grid = self._resolution.beat_value()
        if grid <= 0:
            return beat
        return round(beat / grid) * grid

    def quantize_duration(self, start_beat: float, end_beat: float) -> float:
        """Snap a note duration to the nearest valid length at current resolution.

        Args:
            start_beat: Quantised note start position.
            end_beat: Raw note end position.

        Returns:
            Quantised duration in quarter-note beats.
        """
        raw = end_beat - start_beat
        grid = self._resolution.beat_value()
        snapped = round(raw / grid) * grid
        # Ensure duration is at least one grid unit
        if snapped <= 0:
            snapped = grid
        return snapped

    @staticmethod
    def resolution_labels() -> list[str]:
        """Return all resolution labels in display order (coarse → fine)."""
        return list(_RESOLUTION_FROM_LABEL.keys())
