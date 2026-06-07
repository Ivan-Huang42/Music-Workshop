"""Real-time audio engine built on sounddevice.

Manages the PortAudio output stream and receives note events from the
UI thread via a thread-safe queue. The audio callback runs in a
dedicated high-priority thread and must never block or allocate.
"""

from __future__ import annotations

from queue import Empty, Queue

import numpy as np
import sounddevice as sd
from PySide6.QtCore import QObject, Signal

from music_workshop.audio.mixer import Mixer


class AudioEngine(QObject):
    """Manages the real-time audio output stream and voice dispatch.

    This is the single point of contact between the UI and the audio
    subsystem. UI code calls ``note_on()`` / ``note_off()`` (thread-safe),
    and the audio callback drains those events and mixes audio.

    Signals
    -------
    note_activity(midi_note, is_on) : emitted from the audio callback
        for visual feedback (piano key highlighting).
    """

    note_activity = Signal(int, bool)  # (midi_note, is_on)

    def __init__(
        self,
        sample_rate: int = 48000,
        buffer_size: int = 256,
        channels: int = 2,
        parent: QObject | None = None,
    ):
        super().__init__(parent)
        self._sample_rate = sample_rate
        self._buffer_size = buffer_size
        self._channels = channels
        self._mixer = Mixer(sample_rate)
        self._stream: sd.OutputStream | None = None
        self._event_queue: Queue = Queue()
        self._running = False

    # ------------------------------------------------------------------
    # Public API (call from UI thread — thread-safe)
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Open and start the PortAudio output stream."""
        if self._running:
            return
        self._running = True
        self._stream = sd.OutputStream(
            samplerate=self._sample_rate,
            blocksize=self._buffer_size,
            channels=self._channels,
            dtype="float32",
            callback=self._callback,
            finished_callback=self._on_stream_finished,
        )
        self._stream.start()

    def stop(self) -> None:
        """Stop and close the output stream."""
        self._running = False
        if self._stream is not None:
            if self._stream.active:
                self._stream.stop()
            self._stream.close()
            self._stream = None

    def note_on(self, note: int, velocity: int = 100) -> None:
        """Start a note (thread-safe). *velocity*: 0-127."""
        self._event_queue.put(("note_on", note, velocity))

    def note_off(self, note: int) -> None:
        """Release a note (thread-safe)."""
        self._event_queue.put(("note_off", note))

    def all_notes_off(self) -> None:
        """Silence all active notes immediately."""
        self._event_queue.put(("all_off",))

    def set_instrument(self, name: str) -> None:
        """Switch the current instrument preset."""
        self._event_queue.put(("set_instrument", name))

    @property
    def mixer(self) -> Mixer:
        return self._mixer

    @property
    def sample_rate(self) -> int:
        return self._sample_rate

    @property
    def is_running(self) -> bool:
        return self._running

    # ------------------------------------------------------------------
    # Audio callback (runs in PortAudio real-time thread)
    # ------------------------------------------------------------------

    def _callback(
        self,
        outdata: np.ndarray,
        frames: int,
        time_info,
        status: sd.CallbackFlags,
    ) -> None:
        """Called by PortAudio every ``buffer_size`` frames (~5.3 ms)."""
        if status:
            # Log non-critical underflows but stay alive
            print(f"Audio callback status: {status}", flush=True)

        # Drain all pending events (non-blocking)
        self._drain_events()

        # Generate audio
        mono = self._mixer.process(frames)

        # Write to output buffer
        if self._channels == 1:
            outdata[:, 0] = mono
        else:
            outdata[:, 0] = mono
            outdata[:, 1] = mono

    def _drain_events(self) -> None:
        """Process all pending events from the UI thread."""
        while True:
            try:
                event = self._event_queue.get_nowait()
            except Empty:
                break

            cmd = event[0]
            if cmd == "note_on":
                _, note, vel = event
                voice = self._mixer.start_note(note, vel / 127.0)
                if voice is not None:
                    self.note_activity.emit(note, True)
            elif cmd == "note_off":
                _, note = event
                self._mixer.release_note(note)
                self.note_activity.emit(note, False)
            elif cmd == "all_off":
                self._mixer.all_notes_off()
            elif cmd == "set_instrument":
                _, name = event
                self._mixer.set_instrument(name)

    def _on_stream_finished(self) -> None:
        self._running = False
