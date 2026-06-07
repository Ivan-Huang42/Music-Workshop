"""Built-in instrument presets.

Each top-level variable is an ``InstrumentDefinition`` and is
auto-discovered by ``InstrumentRegistry.initialize()``.

Instrument design rationale
---------------------------
All instruments here are created using pure waveform synthesis
(no samples). Each instrument is defined by:

1. **Synthesis algorithm** — *how* the waveform is generated
   (Karplus-Strong, FM, additive, or modal)
2. **Algorithm parameters** — the specific knobs that shape the timbre
3. **ADSR envelope** — the volume contour (attack → decay → sustain → release)
4. **Effects chain** — post-processing (reverb, chorus, etc.)
"""

from music_workshop.instruments.registry import InstrumentDefinition

# ====================================================================
# Piano — Karplus-Strong
# ====================================================================
# A bright, sustained plucked-string sound. High decay (0.998) gives
# long sustain. Low damping (0.3) preserves high-frequency energy.
# Body resonance adds three characteristic peaks that mimic a piano
# soundboard.
# ====================================================================

ACOUSTIC_GRAND_PIANO = InstrumentDefinition(
    name="acoustic_grand_piano",
    synth_type="karplus_strong",
    params={
        "decay": 0.998,
        "damping": 0.3,
        "pick_position": 0.3,
    },
    envelope={
        "attack": 0.001,
        "decay": 0.3,
        "sustain_level": 0.6,
        "release": 1.0,
    },
    effects_chain=[],
)

# ====================================================================
# Acoustic Guitar — Karplus-Strong
# ====================================================================
# Shorter decay (0.992) and higher damping (0.4) than piano, producing
# the characteristic "pluck and fade" of a steel-string acoustic guitar.
# Body resonance shifted to mid frequencies (100, 300, 600 Hz).
# ====================================================================

ACOUSTIC_GUITAR = InstrumentDefinition(
    name="acoustic_guitar",
    synth_type="karplus_strong",
    params={
        "decay": 0.992,
        "damping": 0.4,
        "pick_position": 0.2,
    },
    envelope={
        "attack": 0.001,
        "decay": 0.15,
        "sustain_level": 0.5,
        "release": 0.3,
    },
    effects_chain=[],
)

# ====================================================================
# Nylon-String Guitar — Karplus-Strong
# ====================================================================
# Warmer, softer version of the acoustic guitar. Higher damping (0.45)
# and a gentle chorus effect to mimic the rounded nylon-string tone.
# ====================================================================

NYLON_GUITAR = InstrumentDefinition(
    name="nylon_guitar",
    synth_type="karplus_strong",
    params={
        "decay": 0.994,
        "damping": 0.45,
        "pick_position": 0.25,
    },
    envelope={
        "attack": 0.002,
        "decay": 0.2,
        "sustain_level": 0.4,
        "release": 0.4,
    },
    effects_chain=[],
)

# ====================================================================
# Bright Piano — Karplus-Strong
# ====================================================================
# A brighter variant with less damping, good for pop melodies.
# ====================================================================

BRIGHT_PIANO = InstrumentDefinition(
    name="bright_piano",
    synth_type="karplus_strong",
    params={
        "decay": 0.997,
        "damping": 0.2,
        "pick_position": 0.15,
    },
    envelope={
        "attack": 0.001,
        "decay": 0.25,
        "sustain_level": 0.55,
        "release": 0.8,
    },
    effects_chain=[],
)

# ====================================================================
# Electric Piano — FM Synthesis (DX7-style)
# ====================================================================
# Classic DX7 electric piano using 2-operator FM: carrier at 1f,
# modulator at 5f. The inharmonic 1:5 ratio produces the characteristic
# bright, bell-like e-piano timbre. Light reverb adds warmth.
# ====================================================================

ELECTRIC_PIANO = InstrumentDefinition(
    name="electric_piano",
    synth_type="fm",
    params={
        "operators": [
            {"freq_ratio": 1.0, "amplitude": 1.0, "feedback": 0.0},
            {"freq_ratio": 5.0, "amplitude": 0.5, "feedback": 0.0},
        ],
        "routing": [(0, [1])],
    },
    envelope={
        "attack": 0.003,
        "decay": 0.3,
        "sustain_level": 0.5,
        "release": 0.8,
    },
    effects_chain=[],
)

# ====================================================================
# Brass — FM Synthesis
# ====================================================================
# 2-operator FM with carrier 1:1 and modulator 1:2, producing a rich
# sawtooth-like spectrum. Slightly delayed attack (20ms) simulates
# breath pressure build-up. Moderate reverb for concert hall presence.
# ====================================================================

BRASS = InstrumentDefinition(
    name="brass",
    synth_type="fm",
    params={
        "operators": [
            {"freq_ratio": 1.0, "amplitude": 1.0, "feedback": 0.0},
            {"freq_ratio": 2.0, "amplitude": 0.5, "feedback": 0.0},
        ],
        "routing": [(0, [1])],
    },
    envelope={
        "attack": 0.02,
        "decay": 0.2,
        "sustain_level": 0.8,
        "release": 0.3,
    },
    effects_chain=[],
)

# ====================================================================
# Church Organ — Additive Synthesis
# ====================================================================
# Drawbar-style organ using 7 harmonic partials at classic organ ratios:
# 16', 8', 5-1/3', 4', 2-2/3', 2', 1-3/5'. No reverb — organ sound
# is naturally dry and direct.
# ====================================================================

CHURCH_ORGAN = InstrumentDefinition(
    name="church_organ",
    synth_type="additive",
    params={
        "partials": [
            {"harmonic": 1.0, "amplitude": 1.0},
            {"harmonic": 2.0, "amplitude": 0.5},
            {"harmonic": 3.0, "amplitude": 0.33},
            {"harmonic": 4.0, "amplitude": 0.25},
            {"harmonic": 5.0, "amplitude": 0.2},
            {"harmonic": 6.0, "amplitude": 0.15},
            {"harmonic": 8.0, "amplitude": 0.1},
        ],
    },
    envelope={
        "attack": 0.05,
        "decay": 0.05,
        "sustain_level": 1.0,
        "release": 0.1,
    },
    effects_chain=[],
)

# ====================================================================
# Marimba — Modal Synthesis
# ====================================================================
# Inharmonic modal ratios (1:4:9.4:16.7) produce the characteristic
# marimba tone. Each mode decays at a different rate: higher modes
# decay faster. A short noise burst simulates the mallet strike.
# ====================================================================

MARIMBA = InstrumentDefinition(
    name="marimba",
    synth_type="modal",
    params={
        "modes": [
            {"frequency_ratio": 1.0, "amplitude": 1.0, "decay_time": 0.5},
            {"frequency_ratio": 4.0, "amplitude": 0.5, "decay_time": 0.3},
            {"frequency_ratio": 9.4, "amplitude": 0.3, "decay_time": 0.2},
            {"frequency_ratio": 16.7, "amplitude": 0.15, "decay_time": 0.1},
        ],
        "strike_noise": 0.3,
        "strike_decay": 0.005,
    },
    envelope={
        "attack": 0.001,
        "decay": 0.01,
        "sustain_level": 0.0,
        "release": 0.5,
    },
    effects_chain=[],
)

# ====================================================================
# Xylophone — Modal Synthesis
# ====================================================================
# Higher, brighter than marimba. Inharmonic ratios: 1:3:6:10:15.
# Shorter decay than marimba for the characteristic dry "click".
# ====================================================================

XYLOPHONE = InstrumentDefinition(
    name="xylophone",
    synth_type="modal",
    params={
        "modes": [
            {"frequency_ratio": 1.0, "amplitude": 1.0, "decay_time": 0.2},
            {"frequency_ratio": 3.0, "amplitude": 0.5, "decay_time": 0.12},
            {"frequency_ratio": 6.0, "amplitude": 0.3, "decay_time": 0.08},
            {"frequency_ratio": 10.0, "amplitude": 0.15, "decay_time": 0.05},
            {"frequency_ratio": 15.0, "amplitude": 0.08, "decay_time": 0.03},
        ],
        "strike_noise": 0.4,
        "strike_decay": 0.003,
    },
    envelope={
        "attack": 0.001,
        "decay": 0.005,
        "sustain_level": 0.0,
        "release": 0.2,
    },
    effects_chain=[],
)

# ====================================================================
# Warm Strings — Additive Synthesis
# ====================================================================
# Simulated string ensemble using lower harmonics with gradual
# roll-off. A light chorus effect adds the characteristic "string
# ensemble" thickness.
# ====================================================================

WARM_STRINGS = InstrumentDefinition(
    name="warm_strings",
    synth_type="additive",
    params={
        "partials": [
            {"harmonic": 1.0, "amplitude": 1.0},
            {"harmonic": 2.0, "amplitude": 0.8},
            {"harmonic": 3.0, "amplitude": 0.6},
            {"harmonic": 4.0, "amplitude": 0.45},
            {"harmonic": 5.0, "amplitude": 0.35},
            {"harmonic": 6.0, "amplitude": 0.25},
            {"harmonic": 7.0, "amplitude": 0.18},
            {"harmonic": 8.0, "amplitude": 0.12},
            {"harmonic": 9.0, "amplitude": 0.08},
        ],
    },
    envelope={
        "attack": 0.08,
        "decay": 0.15,
        "sustain_level": 0.8,
        "release": 0.5,
    },
    effects_chain=[],
)
