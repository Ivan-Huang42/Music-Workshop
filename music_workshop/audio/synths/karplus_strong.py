"""Karplus-Strong physical-model string synthesis."""

import numpy as np

from music_workshop.audio.synths.base import BaseSynthesizer


class KarplusStrongSynthesizer(BaseSynthesizer):
    """Digital waveguide string synthesis via the Karplus-Strong algorithm.

    原理
    ----
    Karplus-Strong 模拟拨弦发声：
      1. 延迟线长度为 ``fs / f0`` 个采样点，用随机噪声初始化
      2. 每个采样点：取当前位置和下一位置的平均值（低通滤波）
      3. 加权衰减后写回延迟线
      4. 输出 = 延迟线当前值

    这导致高频能量比低频衰减更快，模拟真实弦乐器的物理行为。

    Parameters
    ----------
    decay : float
        每采样点衰减系数 (0.99-0.999)。越大延音越长。
    damping : float
        低通滤波系数 (0-1)。0=无滤波(明亮)，1=全滤波(暗淡)。
    pick_position : float
        拨弦位置 (0-1)。0=琴桥，1=琴颈中点。影响泛音分布。
    body_resonance : list[tuple[float, float, float]]
        体共鸣滤波器列表。每个元素为 (中心频率Hz, 带宽Hz, 增益)。
    """

    def __init__(
        self,
        sample_rate: int,
        decay: float = 0.996,
        damping: float = 0.5,
        pick_position: float = 0.5,
        body_resonance: list[tuple[float, float, float]] | None = None,
    ):
        super().__init__(sample_rate)
        self._decay = decay
        self._damping = damping
        self._pick_position = pick_position
        self._body_resonance = body_resonance or []

        self._buffer: np.ndarray | None = None
        self._buffer_len: int = 0
        self._idx: int = 0

    # ------------------------------------------------------------------
    # BaseSynthesizer interface
    # ------------------------------------------------------------------

    def reset(self) -> None:
        self._buffer = None
        self._idx = 0

    def generate(
        self, note: int, velocity: float, num_samples: int, phase: float
    ) -> tuple[np.ndarray, float]:
        freq = self.midi_to_freq(note)
        period = max(int(round(self.sample_rate / freq)), 2)

        # Pitch correction factor — the integer delay length may not be
        # exactly fs/f0, so we apply a small gain correction.
        freq_error = (self.sample_rate / period) / freq if period > 0 else 1.0

        # Lazily initialise the ring buffer (first hit or pitch change).
        if self._buffer is None or self._buffer_len != period:
            # Extended KS: pick-position comb filter colours the initial noise
            noise = self._generate_initial_noise(period)
            self._buffer = noise
            self._buffer_len = period
            self._idx = 0

        out = np.empty(num_samples, dtype=np.float64)

        # Pitch-independent decay adjustment so that low and high notes
        # have comparable perceived sustain length.
        decay_adj = self._decay ** (
            self._buffer_len / (self.sample_rate / freq * self._buffer_len)
            if freq > 0
            else 1.0
        )
        # Simplified: decay_adj = self._decay ** (69 / note) for a gentler curve
        decay_adj = self._decay ** (freq / 130.81)  # scale relative to C3

        for i in range(num_samples):
            # Read current output
            out[i] = self._buffer[self._idx]

            # Two-point moving average (simple lowpass)
            next_idx = (self._idx + 1) % self._buffer_len
            avg = (1.0 - self._damping) * self._buffer[self._idx] + \
                  self._damping * self._buffer[next_idx]

            # Write back with decay
            self._buffer[self._idx] = avg * decay_adj

            # Advance circular index
            self._idx = (self._idx + 1) % self._buffer_len

        # Apply body resonance (simple resonant filter bank)
        if self._body_resonance:
            out = self._apply_body_resonance(out)

        # Normalise to avoid clipping
        peak = np.max(np.abs(out))
        if peak > 1.0:
            out /= peak

        return out * velocity * freq_error, 0.0

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _generate_initial_noise(self, period: int) -> np.ndarray:
        """Generate the initial noise burst that seeds the delay line.

        The pick-position comb filter colours the noise so that different
        playing positions produce different timbres (more/less high end).
        """
        noise = np.random.uniform(-0.5, 0.5, period)

        if self._pick_position > 0.0:
            pk = max(int(period * self._pick_position), 1)
            # Simple comb: y[n] = x[n] - x[n - pk]
            comb = np.zeros_like(noise)
            comb[:pk] = noise[:pk]
            comb[pk:] = noise[pk:] - noise[:-pk]
            noise = comb

        return noise

    def _apply_body_resonance(self, signal: np.ndarray) -> np.ndarray:
        """Apply a bank of simple biquad bandpass filters for body resonance."""
        result = signal.copy()
        for center_hz, _bandwidth, gain in self._body_resonance:
            if gain == 0:
                continue
            # Simple single-pole resonant lowpass approximation
            # y[n] = gain * (x[n] + x[n-1]) / 2 + a1 * y[n-1] - a2 * y[n-2]
            w0 = 2.0 * np.pi * center_hz / self.sample_rate
            q = 10.0  # fixed Q for simplicity
            alpha = np.sin(w0) / (2.0 * q)
            # biquad bandpass coefficients (RBJ cookbook)
            b0 = alpha * gain
            b1 = 0.0
            b2 = -alpha * gain
            a0 = 1.0 + alpha
            a1 = -2.0 * np.cos(w0)
            a2 = 1.0 - alpha

            # Normalise by a0
            b0 /= a0
            b1 /= a0
            b2 /= a0
            a1 /= a0
            a2 /= a0

            # Direct-form I transposed
            x1 = x2 = y1 = y2 = 0.0
            for i in range(len(result)):
                x0 = result[i]
                y0 = b0 * x0 + b1 * x1 + b2 * x2 - a1 * y1 - a2 * y2
                y0 = np.clip(y0, -1.0, 1.0)
                result[i] = y0
                x2, x1 = x1, x0
                y2, y1 = y1, y0

        return result

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def decay(self) -> float:
        return self._decay

    @decay.setter
    def decay(self, value: float) -> None:
        self._decay = value

    @property
    def damping(self) -> float:
        return self._damping

    @damping.setter
    def damping(self, value: float) -> None:
        self._damping = value
