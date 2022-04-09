from enum import Enum, auto
from typing import Callable
from Util.Timestamp import Timestamp as TS


class Phase(Enum):
    One = auto()
    Two = auto()
    Three = auto()
    End = auto()


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

    phase = Phase.One
    __cbList = []

    def __init__(self) -> None:
        """Nope"""
        raise NotImplementedError

    def addCbToPhaseMove(fromPhase: Phase, cb: Callable) -> None:
        """Allows for triggering callbacks when moving to a next phase."""
        CurrentPhase.__cbList.append(CurrentPhase.MoveTrigger(fromPhase, cb))

    def moveToNext(*ignore) -> None:
        """Moves to next phase and runs all relevant callbacks."""
        prevPhase = CurrentPhase.phase
        if CurrentPhase.phase == Phase.One:
            CurrentPhase.phase = Phase.Two
            TS.print("Moving to second phase.")

        elif CurrentPhase.phase == Phase.Two:
            CurrentPhase.phase = Phase.Three
            TS.print("Moving to third phase.")

        else:
            CurrentPhase.phase = Phase.End
            TS.print("Moving to end phase.")

        for cb in CurrentPhase.__cbList:
            cb.run(prevPhase)
