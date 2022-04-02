from enum import Enum, auto
from typing import Callable


class Phase(Enum):
    First = auto()
    Second = auto()
    Third = auto()


class CurrentPhase():
    """Global tracker of the current phase."""

    class MoveTrigger:
        """Smaller wrapper for the callbacks."""

        def __init__(self, fromPhase: Phase, callback: Callable) -> None:
            self.cb = callback
            self.fromPhase = fromPhase

        def run(self, fromPhase: Phase):
            if self.fromPhase == fromPhase:
                self.cb()

    phase = Phase.First
    __cbList = []

    def __init__(self) -> None:
        """Nope"""
        raise NotImplementedError

    def addCbToPhaseMove(fromPhase: Phase, cb: Callable) -> None:
        """Allows for triggering callbacks when moving to a next phase."""
        CurrentPhase.__cbList.append(CurrentPhase.MoveTrigger(fromPhase, cb))

    def moveToNext() -> None:
        """Moves to next phase and runs all relevant callbacks."""
        prevPhase = CurrentPhase.phase
        if CurrentPhase.phase == Phase.First:
            CurrentPhase.phase = Phase.Second
        else:
            CurrentPhase.phase = Phase.Third

        for cb in CurrentPhase.__cbList:
            cb.run(prevPhase)
