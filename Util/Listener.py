# Global class to subscribe to and listen for specific events
from enum import Enum
from Util.Timestamp import Timestamp as TS


class Event(Enum):
    BuyProject = 0
    SpendTrust = 1


class _filteredCallback():
    def __init__(self, callback, filter=None, oneTimer: bool = False) -> None:
        self.cb = callback
        self.filter = filter
        self.once = oneTimer

    def __call__(self, tag: str) -> bool:
        if not self.filter or self.filter(tag):
            self.cb(tag)
            return self.once
        return False


class Listener():
    __eventCollection = {}  # Event : [_filteredCallbacks,]

    def __init__(self) -> None:
        raise NotImplementedError("We don't do that here.")

    def listenTo(event: Event, callback, filter=None, oneTimeOnly: bool = False) -> None:
        entry = Listener.__eventCollection.get(event, False)
        newCb = _filteredCallback(callback, filter, oneTimeOnly)
        if not entry:
            Listener.__eventCollection[event] = [newCb]
            return

        if newCb not in entry:
            entry.append(newCb)

    def notify(event: Event, tag: str) -> None:
        entry = Listener.__eventCollection.get(event, False)
        if not entry:
            return

        removeCbs = []
        for filteredCb in entry:
            if filteredCb(tag):  # Mark filteredCallback for removal
                removeCbs.append(filteredCb)

        if not removeCbs:
            return

        for cb in removeCbs:
            entry.remove(cb)
