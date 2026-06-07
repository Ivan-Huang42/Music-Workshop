"""Real-time waveform and spectrum visualiser widget.

Reads the mixer's most recent audio block and renders:
- Top half: time-domain waveform
- Bottom half: frequency spectrum (FFT)

Safe for real-time use — does NOT trigger audio processing.
"""

from __future__ import annotations

import numpy as np
from PySide6.QtCore import QTimer
from PySide6.QtGui import QColor, QLinearGradient, QPainter, QPen
from PySide6.QtWidgets import QWidget

from music_workshop.audio.mixer import Mixer


class WaveformWidget(QWidget):
    """Displays real-time waveform and spectrum from the audio mixer.

    Polls ``mixer.last_output`` for the latest audio block and renders
    it visually. Inactive (no keys pressed) shows a flat line.

    Args:
        mixer: The Mixer instance to read audio from.
        parent: Parent Qt widget.
    """

    def __init__(self, mixer: Mixer, parent: QWidget | None = None):
        super().__init__(parent)
        self._mixer = mixer
        self._wave_buffer = np.zeros(2048, dtype=np.float64)
        self._spec_buffer = np.zeros(256, dtype=np.float64)
        self._active = False

        # Poll timer — reads the mixer's last output block
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._poll_and_update)
        self._timer.start(50)  # ~20 fps

        self.setMinimumHeight(150)

    def _poll_and_update(self) -> None:
        """Read the latest audio from the mixer and redraw."""
        block = self._mixer.last_output
        if block is not None and len(block) > 0 and np.max(np.abs(block)) > 0.001:
            self._active = True
            n = min(len(block), 2048)
            # Shift + append
            self._wave_buffer[:-n] = self._wave_buffer[n:]
            self._wave_buffer[-n:] = block[-n:]

            # FFT spectrum
            windowed = block[-min(len(block), 1024):] * np.hanning(min(len(block), 1024))
            spec = np.abs(np.fft.rfft(windowed))
            spec = 20 * np.log10(spec / (len(spec) + 1e-12) + 1e-12)
            # Decimate to 256 bins
            if len(spec) > 256:
                spec = spec[:256]
            self._spec_buffer = spec
        else:
            self._active = False

        self.update()

    # ------------------------------------------------------------------
    # Painting
    # ------------------------------------------------------------------

    def paintEvent(self, event) -> None:  # noqa: ARG002
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()
        mid = h // 2

        # Background
        painter.fillRect(0, 0, w, h, QColor(14, 14, 28))

        if not self._active:
            painter.setPen(QColor(60, 60, 80))
            painter.drawText(w // 2 - 80, mid - 4, "Play a note to see waveform")
            return

        # Waveform (top half)
        self._draw_waveform(painter, w, mid)

        # Separator
        painter.setPen(QPen(QColor(50, 50, 70), 1))
        painter.drawLine(0, mid, w, mid)

        # Spectrum (bottom half)
        self._draw_spectrum(painter, w, mid, h)

        # Labels
        painter.setPen(QColor(100, 100, 130))
        painter.setFont(self.font())
        painter.drawText(6, 14, "Waveform")
        painter.drawText(6, mid + 14, "Spectrum")

    def _draw_waveform(self, painter: QPainter, w: int, h: int) -> None:
        """Draw time-domain waveform."""
        n = len(self._wave_buffer)
        # Centre line
        painter.setPen(QPen(QColor(35, 35, 55), 1))
        painter.drawLine(0, h // 2, w, h // 2)

        # Waveform curve
        painter.setPen(QPen(QColor(0, 200, 255), 1.2))
        ox, oy = 0, h // 2
        for i in range(1, n):
            x = int(i / n * w)
            y = int(h // 2 - self._wave_buffer[i] * (h // 2 - 8))
            if 0 <= y < h:
                painter.drawLine(ox, oy, x, y)
            ox, oy = x, y

    def _draw_spectrum(self, painter: QPainter, w: int, mid_y: int, h: int) -> None:
        """Draw frequency spectrum as vertical bars."""
        n = len(self._spec_buffer)
        bar_h = h - mid_y
        bar_w = max(2, w // n - 1)

        grad = QLinearGradient(0, mid_y, 0, h)
        grad.setColorAt(0.0, QColor(255, 80, 80))
        grad.setColorAt(0.5, QColor(255, 200, 80))
        grad.setColorAt(1.0, QColor(80, 200, 80))

        for i in range(n):
            db = self._spec_buffer[i]
            height = int(max(0, (db + 80) / 80.0 * (bar_h - 12)))
            x = int(i / n * w)
            y = h - height - 4
            painter.fillRect(x, y, bar_w, height, grad)

    def close(self) -> None:
        self._timer.stop()
