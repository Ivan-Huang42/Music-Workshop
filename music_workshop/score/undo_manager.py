"""Undo/redo manager for score operations.

Stores note snapshots as lists of (pitch, offset, duration, velocity, part_name)
tuples. This avoids issues with music21 serialisation format compatibility.
"""

from __future__ import annotations

from typing import Any


class UndoManager:
    """Manages undo/redo history as note-insertion rollbacks.

    Args:
        max_history: Maximum undo steps to retain.
    """

    def __init__(self, max_history: int = 50):
        self._max_history = max_history
        self._undo_stack: list[list[tuple]] = []
        self._redo_stack: list[list[tuple]] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def snapshot(self, notes: list[tuple]) -> None:
        """Store a snapshot of the current note list.

        Each tuple: (midi_pitch, start_beat, duration_beats, velocity, part_name)
        """
        self._undo_stack.append(list(notes))
        self._redo_stack.clear()
        if len(self._undo_stack) > self._max_history:
            self._undo_stack.pop(0)

    def undo(self, notes: list[tuple]) -> list[tuple] | None:
        """Restore the previous state.

        Args:
            notes: Current note list (will be saved to redo stack).

        Returns:
            Previous note list, or None if nothing to undo.
        """
        if not self._undo_stack:
            return None
        self._redo_stack.append(list(notes))
        return list(self._undo_stack.pop())

    def redo(self, notes: list[tuple]) -> list[tuple] | None:
        """Restore the next state.

        Args:
            notes: Current note list (will be saved to undo stack).

        Returns:
            Next note list, or None if nothing to redo.
        """
        if not self._redo_stack:
            return None
        self._undo_stack.append(list(notes))
        return list(self._redo_stack.pop())

    @property
    def can_undo(self) -> bool:
        return len(self._undo_stack) > 1  # Keep initial state

    @property
    def can_redo(self) -> bool:
        return len(self._redo_stack) > 0

    def clear(self) -> None:
        self._undo_stack.clear()
        self._redo_stack.clear()
