#!/usr/bin/env python3
"""Waveform & spectrum visualiser for Music Workshop.

Shows the generated waveform and frequency spectrum of any instrument
in real time. Useful for understanding how synthesis parameters affect
the sound.

Usage
-----
    .venv/Scripts/python tools/waveform_viewer.py

Controls
--------
    1-0  : switch instrument (as labelled)
    SPACE : play a note (C4)
    ← →   : change note pitch
    ↑ ↓   : change octave
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np

# ── matplotlib ──────────────────────────────────────────────────────
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.patches import Rectangle

# ── Music Workshop ──────────────────────────────────────────────────
from music_workshop.app import startup
from music_workshop.instruments.registry import InstrumentRegistry
from music_workshop.audio.synths.karplus_strong import KarplusStrongSynthesizer
from music_workshop.audio.voice import Voice
from music_workshop.audio.envelope import ADSREnvelope

startup()
InstrumentRegistry.initialize()
instruments = InstrumentRegistry.list_instruments()

# ── State ───────────────────────────────────────────────────────────
SAMPLE_RATE = 48000
DURATION = 1.0  # seconds
NUM_SAMPLES = int(SAMPLE_RATE * DURATION)

current_inst_idx = 0
current_note = 60  # C4
note_names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

# Generate audio buffer
audio_buffer = np.zeros(NUM_SAMPLES)
need_regenerate = True


def midi_note_name(n):
    return f"{note_names[n % 12]}{n // 12 - 1}"


def generate_audio():
    global audio_buffer, need_regenerate
    if not need_regenerate:
        return
    name = instruments[current_inst_idx]
    defn = InstrumentRegistry.get(name)

    # Create voice and envelope
    voice = Voice(SAMPLE_RATE)
    voice.trigger(current_note, 0.8, defn)

    # Collect samples
    samples = []
    remaining = NUM_SAMPLES
    while remaining > 0:
        block = voice.generate(min(remaining, 4096))
        if block is None:
            break
        samples.append(block)
        remaining -= len(block)

    if samples:
        audio_buffer = np.concatenate(samples)[:NUM_SAMPLES]
    else:
        audio_buffer = np.zeros(NUM_SAMPLES)

    # Normalise
    peak = np.max(np.abs(audio_buffer))
    if peak > 0:
        audio_buffer /= peak

    need_regenerate = False


# ── Matplotlib figure ───────────────────────────────────────────────
fig, (ax_wave, ax_spec) = plt.subplots(
    2, 1, figsize=(14, 7), facecolor="#1a1a2e"
)
fig.canvas.manager.set_window_title("Music Workshop — Waveform Viewer")

# Time-domain axis
ax_wave.set_facecolor("#16213e")
ax_wave.set_xlim(0, NUM_SAMPLES / SAMPLE_RATE * 1000)
ax_wave.set_ylim(-1.5, 1.5)
ax_wave.set_xlabel("Time (ms)", color="#ccc")
ax_wave.set_ylabel("Amplitude", color="#ccc")
ax_wave.tick_params(colors="#ccc")
ax_wave.grid(alpha=0.15, color="#fff")
ax_wave_title = ax_wave.set_title("", color="#fff", fontsize=12)
(line_wave,) = ax_wave.plot([], [], "#00d2ff", lw=0.6)

# Frequency-domain axis
ax_spec.set_facecolor("#16213e")
ax_spec.set_xlim(20, 8000)
ax_spec.set_ylim(-80, 0)
ax_spec.set_xlabel("Frequency (Hz)", color="#ccc")
ax_spec.set_ylabel("Magnitude (dB)", color="#ccc")
ax_spec.tick_params(colors="#ccc")
ax_spec.grid(alpha=0.15, color="#fff")
ax_spec.set_xscale("log")
(line_spec,) = ax_spec.plot([], [], "#ff6b6b", lw=0.6)
(fill_spec,) = ax_spec.fill_between([], [], 0, alpha=0.2, color="#ff6b6b")

# Info box
info_text = ax_spec.text(
    0.98, 0.95, "", transform=ax_spec.transAxes,
    color="#ccc", fontsize=10, ha="right", va="top",
    bbox=dict(boxstyle="round,pad=0.5", facecolor="#1a1a2e", alpha=0.8),
)


def update_plot(frame):
    global need_regenerate
    generate_audio()
    t_ms = np.arange(NUM_SAMPLES) / SAMPLE_RATE * 1000
    name = instruments[current_inst_idx]

    # Show first 100ms of waveform
    show_ms = min(100, DURATION * 1000)
    show_samples = int(show_ms / 1000 * SAMPLE_RATE)
    line_wave.set_data(t_ms[:show_samples], audio_buffer[:show_samples])

    # FFT spectrum
    window = np.hanning(NUM_SAMPLES)
    fft_data = audio_buffer * window
    spectrum = np.fft.rfft(fft_data)
    magnitude = np.abs(spectrum)
    freqs = np.fft.rfftfreq(NUM_SAMPLES, 1 / SAMPLE_RATE)

    # Keep only up to 8 kHz
    mask = freqs <= 8000
    mag_db = 20 * np.log10(magnitude / (len(magnitude) + 1e-12) + 1e-12)
    line_spec.set_data(freqs[mask], mag_db[mask])
    ax_spec.collections.clear()
    ax_spec.fill_between(freqs[mask], mag_db[mask], -80, alpha=0.15, color="#ff6b6b")

    # Update title
    note_name = midi_note_name(current_note)
    ax_wave_title.set_text(
        f"[{current_inst_idx + 1}/{len(instruments)}] {name}  —  "
        f"{note_name} (MIDI {current_note}) "
        f"—  FFT: {freqs[np.argmax(magnitude)]:.1f} Hz"
    )

    # Detect harmonics
    peak_mask = magnitude > np.max(magnitude) * 0.05
    peak_indices = np.where(peak_mask)[0]
    if len(peak_indices) > 0 and len(peak_indices) < 50:
        peak_freqs = freqs[peak_indices]
        info_str = f"Partials: "
        visible = peak_freqs[peak_freqs <= 8000][:12]
        if len(visible) > 0:
            fund = visible[0]
            ratios = [f"{f / fund:.1f}x" for f in visible]
            info_str += "  ".join(f"{f:.0f}Hz({r})" for f, r in zip(visible, ratios))
        else:
            info_str += "(noise / no clear fundamental)"
        info_text.set_text(info_str)
    else:
        info_text.set_text("(complex spectrum / noise)")

    return line_wave, line_spec, info_text


# ── Keyboard input ──────────────────────────────────────────────────
def on_key(event):
    global current_inst_idx, current_note, need_regenerate
    if event.key == "escape":
        plt.close()
        return

    # Instrument switching (1-0)
    if event.key in "1234567890":
        idx = int(event.key) - 1 if event.key != "0" else 9
        if idx < len(instruments):
            current_inst_idx = idx
            need_regenerate = True

    # Note selection
    if event.key == "left":
        current_note = max(24, current_note - 1)
        need_regenerate = True
    elif event.key == "right":
        current_note = min(96, current_note + 1)
        need_regenerate = True
    elif event.key == "up":
        current_note = min(96, current_note + 12)
        need_regenerate = True
    elif event.key == "down":
        current_note = max(24, current_note - 12)
        need_regenerate = True
    elif event.key == " ":
        need_regenerate = True


fig.canvas.mpl_connect("key_press_event", on_key)

# ── Controls legend ─────────────────────────────────────────────────
legend = (
    f"{'  |  '.join(f'[{i+1}] {n}' for i, n in enumerate(instruments[:5]))}\n"
    f"{'  |  '.join(f'[{i+1}] {n}' for i, n in enumerate(instruments[5:10]))}\n"
    f"[← →] Pitch  [↑ ↓] Octave  [SPACE] Play  [ESC] Exit"
)
ax_spec.text(
    0.02, 0.02, legend, transform=ax_spec.transAxes,
    color="#888", fontsize=8, va="bottom", ha="left",
    bbox=dict(boxstyle="round,pad=0.3", facecolor="#1a1a2e", alpha=0.7),
)

# ── Start ───────────────────────────────────────────────────────────
ani = FuncAnimation(fig, update_plot, interval=200, cache_frame_data=False)
plt.tight_layout()
plt.show()
