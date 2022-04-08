from Webpage.PageState.PageActions import PageActions
from Webpage.PageState.PageInfo import PageInfo
from enum import Enum, auto


class SettingType(Enum):
    Speed = auto()
    Explore = auto()
    Replicate = auto()
    Hazard = auto()
    Factory = auto()
    Harvester = auto()
    Wire = auto()
    Combat = auto()


class TrustSettingEntry():
    """Helper class to track the trust setting of a single entry."""

    def __init__(self, pageActions: PageActions, buttonDown: str, buttonUp: str) -> None:
        self.buttonDown = lambda: pageActions.pressButton(buttonDown)
        self.buttonUp = lambda: pageActions.pressButton(buttonUp)
        self.currentValue = 0

    def down(self) -> None:
        """If possible, lower the trust value with one point."""
        if self.currentValue > 0:
            self.buttonDown()
            self.currentValue -= 1

    def up(self) -> None:
        """Increase the trust value with one point. No check will be made if any are actually available."""
        self.buttonUp()
        self.currentValue += 1

    def val(self) -> int:
        """Return the current value of the trust setting."""
        return self.currentValue


class ProbeTrustSettings():
    """Keeps track of the trust settings of the probes."""

    def __init__(self, pageActions: PageActions) -> None:
        buttonPairs = [
            ["LowerSpeed", "RaiseSpeed"],
            ["LowerExploration", "RaiseExploration"],
            ["LowerReplication", "RaiseReplication"],
            ["LowerHazard", "RaiseHazard"],
            ["LowerFactory", "RaiseFactory"],
            ["LowerHarvester", "RaiseHarvester"],
            ["LowerWire", "RaiseWire"],
            ["LowerCombat", "RaiseCombat"]]
        settingList = [enum for enum in SettingType]
        assert len(buttonPairs) == len(settingList)

        # Map each enum against their entry.
        self.settings = {settingList[n]: TrustSettingEntry(
            pageActions, buttonPairs[n][0], buttonPairs[n][1], ) for n in range(len(buttonPairs))}

    def set(self, setting: SettingType, newValue: int) -> None:
        """Change a single setting to a new value."""
        # TODO: Perhaps this should do all settings at once, since this class tracks their values too.

        entry = self.settings[setting]
        currValue = entry.val()

        if currValue == newValue:
            return

        delta = currValue - newValue
        for _ in range(abs(delta)):
            entry.up() if delta < 0 else entry.down()

    def val(self):
        """Returns a dict of {enum: value} with all available settings."""
        valmap = {setting: entry.val()
                  for setting, entry in self.settings.items()}
        return valmap
