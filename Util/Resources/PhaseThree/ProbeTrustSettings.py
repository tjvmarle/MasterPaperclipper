from Util.Listener import Event, Listener
from Webpage.PageState.PageActions import PageActions

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

    def __init__(self, pageActions: PageActions, currentTrust: int) -> None:
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
        self.availTrust = currentTrust

        # Map each enum against their entry.
        self.settings = {settingList[n]: TrustSettingEntry(
            pageActions, buttonPairs[n][0], buttonPairs[n][1], ) for n in range(len(buttonPairs))}

        Listener.listenTo(Event.ButtonPressed, self.__increaseTrust, "BuyProbeTrust", False)

    def __increaseTrust(self, _: str) -> None:
        self.availTrust += 1

    def setTrust(self, speed: int, explore: int, replicate: int, hazard: int, factory: int, harvester: int, wire: int,
                 combat: int = 0) -> bool:
        """Set the new trust values. The values will first be decreased so enough trust is available for the remaining 
        increases. Returns False if not enough trust is available."""

        mappedValues = {SettingType.Speed: speed, SettingType.Explore: explore, SettingType.Replicate: replicate,
                        SettingType.Hazard: hazard, SettingType.Factory: factory, SettingType.Harvester: harvester,
                        SettingType.Wire: wire, SettingType.Combat: combat}
        total = sum(mappedValues.values())

        if total > self.availTrust:
            return False

        currValues = self.__val()
        assert len(currValues) == len(mappedValues)

        # List together the type, newvalue and delta, sorted with most negative delta first.
        deltaSets = [(type, newValue, newValue - currValues[type])
                     for type, newValue in mappedValues.items()]

        deltaSets.sort(key=lambda tuple: tuple[2])

        for type, newValue, _ in deltaSets:
            self.__set(type, newValue)

    def __set(self, setting: SettingType, newValue: int) -> None:
        """Change a single setting to a new value."""
        # TODO: Perhaps this should do all settings at once, since this class tracks their values too.

        entry = self.settings[setting]
        currValue = entry.val()

        if currValue == newValue:
            return

        delta = currValue - newValue
        for _ in range(abs(delta)):
            entry.up() if delta < 0 else entry.down()

    def __val(self):
        """Returns a dict of {enum: value} with all available settings."""
        valmap = {setting: entry.val()
                  for setting, entry in self.settings.items()}
        return valmap
