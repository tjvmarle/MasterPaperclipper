from enum import Enum, auto
from typing import Callable, List
from Util.Timestamp import Timestamp as TS
import inspect


class Event(Enum):
    BuyProject = auto()
    ButtonPressed = auto()


class Listener():
    """Static class to allow for notifications on project acquisitions and specific buttonpresses."""

    class __filteredCallback():
        """Wrapper class for the event triggers."""

        def __init__(self, callback, filter: Callable = None, oneTimer: bool = False) -> None:
            # TODO: Change oneTime into a decrementing counter. Take -1 for 'infinite'.
            self.cb = callback
            self.filter = filter
            self.once = oneTimer

        def __call__(self, tag: str) -> bool:
            """Checks if the tag is relevant and executes the callback if it is."""

            if self.filter(tag):
                # Check if the callback accepts a string and only pass the tag if it does.
                argList = inspect.signature(self.cb).parameters.values()
                lenCheck = len(argList) == 1
                listCheck = ([entry.annotation == str for entry in argList] == [True])  # Bit ugly ¯\_(ツ)_/¯
                if lenCheck and listCheck:
                    self.cb(tag)
                else:
                    self.cb()

                return self.once
            return False

    __eventCollection = {}  # Event : [_filteredCallbacks,]

    def __init__(self) -> None:
        """Due to its global nature only static functionality is allowed."""
        raise NotImplementedError("We don't do that here.")

    def listenTo(event: Event, callback: Callable, filter, oneTimeOnly: bool = False) -> None:
        """Add a callback to track a specific event."""
        entry: List[Callable] = Listener.__eventCollection.get(event, False)

        if isinstance(filter, str):
            # Works for both Project- and Button names
            def Cbfilter(strInput): return strInput == filter
        else:
            Cbfilter = filter

        newCb = Listener.__filteredCallback(callback, Cbfilter, oneTimeOnly)
        if not entry:
            Listener.__eventCollection[event] = [newCb]
            return

        if newCb not in entry:
            entry.append(newCb)

    def notify(event: Event, tag: str) -> None:
        """Run all relevant callbacks for a specific event."""
        entry = Listener.__eventCollection.get(event, False)
        if not entry:
            return

        removeCbs = []
        for filteredCb in entry:
            if filteredCb(tag):
                removeCbs.append(filteredCb)

        if not removeCbs:
            return

        for cb in removeCbs:
            entry.remove(cb)
