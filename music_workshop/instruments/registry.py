"""Instrument definitions and registry.

An *instrument definition* is a pure-data specification of how a sound
should be synthesised: which algorithm, what parameters, the ADSR
envelope, and an effects chain.

The *InstrumentRegistry* stores all known definitions and acts as a
simple factory for creating synthesizer instances.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class InstrumentDefinition:
    """Pure-data specification for one instrument voice.

    Attributes
    ----------
    name: Human-readable identifier (e.g. ``"acoustic_grand_piano"``).
    synth_type: Key selecting a synthesizer class
        (``"karplus_strong"``, ``"fm"``, ``"additive"``, ``"modal"``).
    params: Keyword arguments forwarded to the synthesizer constructor.
    envelope: ADSR as ``{"attack": ..., "decay": ..., "sustain_level": ...,
        "release": ...}`` (times in seconds).
    effects_chain: List of effect descriptors, each
        ``{"type": ..., ...kwargs}``.
    """

    name: str
    synth_type: str
    params: dict[str, Any] = field(default_factory=dict)
    envelope: dict[str, float] = field(default_factory=dict)
    effects_chain: list[dict[str, Any]] = field(default_factory=list)


_SYNTH_CLASSES: dict[str, type] = {}


def _lazy_import_synth_classes():
    """Import synth classes only when first needed (avoids circular imports)."""
    if _SYNTH_CLASSES:
        return
    from music_workshop.audio.synths.karplus_strong import (  # noqa: PLC0415
        KarplusStrongSynthesizer,
    )
    from music_workshop.audio.synths.fm import FMSynthesizer, FMOperator  # noqa: PLC0415
    from music_workshop.audio.synths.additive import AdditiveSynthesizer, Partial  # noqa: PLC0415
    from music_workshop.audio.synths.modal import ModalSynthesizer, Mode  # noqa: PLC0415

    _SYNTH_CLASSES["karplus_strong"] = KarplusStrongSynthesizer
    _SYNTH_CLASSES["fm"] = FMSynthesizer
    _SYNTH_CLASSES["additive"] = AdditiveSynthesizer
    _SYNTH_CLASSES["modal"] = ModalSynthesizer


class InstrumentRegistry:
    """Singleton registry of instrument definitions + synth factory."""

    _definitions: dict[str, InstrumentDefinition] = {}

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    @classmethod
    def initialize(cls) -> None:
        """Load all built-in presets from ``music_workshop.instruments.presets``."""
        from music_workshop.instruments import presets as _presets  # noqa: PLC0415

        for name in dir(_presets):
            val = getattr(_presets, name)
            if isinstance(val, InstrumentDefinition):
                cls._definitions[val.name] = val

    @classmethod
    def register(cls, defn: InstrumentDefinition) -> None:
        """Register a single definition (useful for user presets)."""
        cls._definitions[defn.name] = defn

    # ------------------------------------------------------------------
    # Lookup
    # ------------------------------------------------------------------

    @classmethod
    def get(cls, name: str) -> InstrumentDefinition | None:
        """Return the definition, or ``None`` if not found."""
        return cls._definitions.get(name)

    @classmethod
    def list_instruments(cls) -> list[str]:
        """Return names of all registered instruments."""
        return list(cls._definitions.keys())

    # ------------------------------------------------------------------
    # Factory
    # ------------------------------------------------------------------

    @classmethod
    def create_synthesizer(
        cls, synth_type: str, params: dict[str, Any], sample_rate: int
    ):
        """Create a synthesizer instance matching *synth_type*.

        Args:
            synth_type: Key like ``"karplus_strong"``, ``"fm"``, etc.
            params: Parameters forwarded to the synth constructor.
            sample_rate: Audio sample rate.

        Returns:
            A ``BaseSynthesizer`` subclass instance.
        """
        _lazy_import_synth_classes()

        if synth_type == "karplus_strong":
            from music_workshop.audio.synths.karplus_strong import (  # noqa: PLC0415
                KarplusStrongSynthesizer,
            )
            return KarplusStrongSynthesizer(sample_rate, **params)

        if synth_type == "fm":
            from music_workshop.audio.synths.fm import (  # noqa: PLC0415
                FMSynthesizer, FMOperator,
            )
            operators = [FMOperator(**op) for op in params.get("operators", [])]
            routing = [(c, m) for c, m in params.get("routing", [])]
            return FMSynthesizer(sample_rate, operators, routing)

        if synth_type == "additive":
            from music_workshop.audio.synths.additive import (  # noqa: PLC0415
                AdditiveSynthesizer, Partial,
            )
            partials = [Partial(**p) for p in params.get("partials", [])]
            return AdditiveSynthesizer(sample_rate, partials)

        if synth_type == "modal":
            from music_workshop.audio.synths.modal import (  # noqa: PLC0415
                ModalSynthesizer, Mode,
            )
            modes = [Mode(**m) for m in params.get("modes", [])]
            strike_noise = params.get("strike_noise", 0.3)
            strike_decay = params.get("strike_decay", 0.005)
            return ModalSynthesizer(sample_rate, modes, strike_noise, strike_decay)

        msg = f"Unknown synthesizer type: {synth_type!r}"
        raise ValueError(msg)
