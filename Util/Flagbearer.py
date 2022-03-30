from typing import Callable, Any


class FlagBearer():
    """Class to take care of all the different bool flags in the modules"""

    def __init__(self, true: tuple = None, false: tuple = None) -> None:
        self.flags = {}
        if true:
            for entry in true:
                self.flags[entry] = True

        if false:
            for entry in false:
                self.flags[entry] = False

    def set(self, flagId: Any, flagValue: bool):
        """This one is mostly for callback purposes."""
        self.flags[flagId] = flagValue

    def __setitem__(self, key, value) -> None:
        self.flags[key] = value

    def __getitem__(self, key) -> bool:
        return self.flags[key]
