"""QWERTY keyboard to MIDI note mapper.

Maps computer keyboard keys to musical notes using the **classic two-row
piano layout** used by most virtual pianos and music production tools.

Layout
------
Middle row (A–L) — main playing area, white keys:
    A→C4  S→D4  D→E4  F→F4  G→G4  H→A4  J→B4  K→C5  L→D5  ;→E5

Upper row (W–P) — black keys/accidentals:
    W→C#4  E→D#4  T→F#4  Y→G#4  U→A#4  O→C#5  P→D#5

Bottom row (Z–/) — lower extension, same white keys one octave offset:
    Z→B3   X→C4   C→D4   V→E4   B→F4   N→G4   M→A4  ,→B4  .→C5  /→D5

Octave shift: Shift+Z (down) / Shift+X (up)
Velocity: Ctrl = piano (60), Alt = mezzo-forte (80), none = forte (100)

Note: A and X both map to C4 (redundancy is intentional — two physical
positions for middle C).
"""

from PySide6.QtCore import Qt


class KeyboardMapper:
    """Maps QWERTY key events to MIDI note numbers with modifiers."""

    # Classic two-row QWERTY piano layout.
    # Middle row = white keys (A-J) + black keys on the QWERTY row above.
    # Bottom row = lower extension (same notes, starting from B3).
    _KEYMAP: dict[int, int] = {
        # --- Row 2 (ASDFGHJKL;) — white keys, main area ---
        Qt.Key_A: 60,  # C4
        Qt.Key_S: 62,  # D4
        Qt.Key_D: 64,  # E4
        Qt.Key_F: 65,  # F4
        Qt.Key_G: 67,  # G4
        Qt.Key_H: 69,  # A4
        Qt.Key_J: 71,  # B4
        Qt.Key_K: 72,  # C5
        Qt.Key_L: 74,  # D5
        Qt.Key_Semicolon: 76,  # E5
        # --- Row 1 (W E T Y U O P) — black keys ---
        Qt.Key_W: 61,  # C#4
        Qt.Key_E: 63,  # D#4
        Qt.Key_T: 66,  # F#4
        Qt.Key_Y: 68,  # G#4
        Qt.Key_U: 70,  # A#4
        Qt.Key_O: 73,  # C#5
        Qt.Key_P: 75,  # D#5
        # --- Row 3 (ZXCVBNM,./) — lower extension ---
        Qt.Key_Z: 59,  # B3  (one below middle C)
        Qt.Key_X: 60,  # C4
        Qt.Key_C: 62,  # D4
        Qt.Key_V: 64,  # E4
        Qt.Key_B: 65,  # F4
        Qt.Key_N: 67,  # G4
        Qt.Key_M: 69,  # A4
        Qt.Key_Comma: 71,  # B4
        Qt.Key_Period: 72,  # C5
        Qt.Key_Slash: 74,  # D5
    }

    # Octave control (pressed via Shift modifier)
    _OCTAVE_DOWN_KEY = Qt.Key_Z
    _OCTAVE_UP_KEY = Qt.Key_X

    # Int values of modifier enums (PySide6 compatibility)
    _SHIFT: int = getattr(Qt.ShiftModifier, "value", 1)
    _CTRL: int = getattr(Qt.ControlModifier, "value", 4)
    _ALT: int = getattr(Qt.AltModifier, "value", 8)

    def __init__(self):
        self._octave_shift: int = 0  # ±n octaves from base

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def key_to_note(self, key: int, modifiers) -> int | None:
        """Convert a key press to a MIDI note number.

        Returns ``None`` if the key is not a musical note key
        (e.g. it's an octave-shift key, which is handled internally).
        """
        # Normalise modifiers to int for cross-platform compatibility.
        if isinstance(modifiers, int):
            mods = modifiers
        else:
            mods = int(getattr(modifiers, "value", 0))

        # Octave shift (Shift+Z = down, Shift+X = up)
        if mods & self._SHIFT:
            if key == self._OCTAVE_DOWN_KEY:
                self._octave_shift = max(-3, self._octave_shift - 1)
                return None
            if key == self._OCTAVE_UP_KEY:
                self._octave_shift = min(5, self._octave_shift + 1)
                return None

        base = self._KEYMAP.get(key)
        if base is None:
            return None
        return base + (self._octave_shift * 12)

    @staticmethod
    def modifier_to_velocity(modifiers) -> int:
        """Map modifier keys to MIDI velocity (0-127).

        - **Ctrl**: 60  (piano, soft)
        - **Alt**:  80  (mezzo-forte)
        - **None**: 100 (forte, default)
        """
        mods = modifiers.value if hasattr(modifiers, 'value') else int(modifiers)
        if mods & KeyboardMapper._CTRL:
            return 60
        if mods & KeyboardMapper._ALT:
            return 80
        return 100

    @property
    def octave_shift(self) -> int:
        return self._octave_shift
