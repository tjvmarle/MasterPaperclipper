from Webpage.PageState.PageActions import PageActions
from Webpage.PageState.PageInfo import PageInfo
from Util.Timestamp import Timestamp as TS
from Util.Listener import Event, Listener
from enum import Enum, auto
from multiprocessing import Lock
import time
import math


class SettingType(Enum):
    Speed = auto()
    Explore = auto()
    Replicate = auto()
    Hazard = auto()
    Factory = auto()
    Harvester = auto()
    Wire = auto()
    Combat = auto()


class SettingEntry():

    def __init__(self, pageActions: PageActions, buttonDown: str, buttonUp: str) -> None:
        self.buttonDown = lambda: pageActions.pressButton(buttonDown)
        self.buttonUp = lambda: pageActions.pressButton(buttonUp)
        self.currentValue = 0

    def down(self) -> None:
        if self.currentValue > 0:
            self.buttonDown()
            self.currentValue -= 1

    def up(self) -> None:
        self.buttonUp()
        self.currentValue += 1

    def val(self) -> int:
        return self.currentValue


class ProbeSettings():

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

        self.settings = {settingList[n]: SettingEntry(
            pageActions, buttonPairs[n][0], buttonPairs[n][1], ) for n in range(len(buttonPairs))}  # Pythonic?
        TS.print(f"self.settings: {self.settings}")

    def set(self, setting: SettingType, newValue: int) -> None:
        entry = self.settings[setting]
        currValue = entry.val()

        if currValue == newValue:
            return

        delta = currValue - newValue
        for _ in range(abs(delta)):
            entry.up() if delta < 0 else entry.down()

    def val(self):
        """ Returns a dict of {enum: value} """

        valmap = {setting: entry.val() for setting, entry in self.settings.items()}
        return valmap


# Some added safety since we're working with seperate, timed threads
probeSettingMutex = Lock()


class ProbeBalancer():

    def __lockedCall(self, callBack, *args) -> None:
        with probeSettingMutex:
            callBack(*args)

    def __namingTheBattles(self, _: str) -> None:
        self.fightingForHonor = True
        self.__setToCreatingProbes()

    def __combatBought(self, _: str) -> None:
        self.combatEnabled = True
        self.__setToCreatingProbes()

    def __oodaLoopBought(self, _: str) -> None:
        self.oodaLoopEnabled = True
        self.__setToCreatingProbes()

    def __threnodyBought(self, _: str) -> None:
        self.threnodyCounter += 1

    def __setToCreatingDrones(self) -> None:
        """Change probe settings to produce a large amount of drones. Usually done intermittently to quickly increase swarm power."""
        availtrust = self.currTrust - 5
        harvesterTrust = math.ceil(availtrust / 2)
        wireTrust = math.floor(availtrust / 2)

        self.setTrust(0, 0, 3, 2, 0, harvesterTrust, wireTrust)

    def __setToCreatingProbes(self) -> None:
        """Change probe settings to produce as many probes as possible. This is more or less the default setting."""
        speed = 2 if self.oodaLoopEnabled else 0

        if self.combatEnabled:
            self.setTrust(speed, 0, self.currTrust - speed - 11, 6, 0, 0, 0, 5)
        elif self.fightingForHonor:
            self.setTrust(speed, 0, self.currTrust - speed - 13, 6, 0, 0, 0, 5)
        else:
            self.setTrust(0, 0, self.currTrust - 6, 6, 0, 0, 0)

    def __setToMatter(self) -> None:
        """Change probe settings to produce some factories and explore for some matter. We only need a minimal amount of factories, because production will be mostly bottlenecked by low swarm productivity."""
        # TODO: Instead of checking AvailMatter, check AvailClips vs current nr of Probes
        matter = self.info.get("AvailMatter").text
        if matter != "0":
            # No need to acquire more matter
            TS.print(f"Skipping matter, current available matter is {matter} g.")
            return
        TS.print("Acquiring matter.")

        availableTrust = self.currTrust - 7
        speedTrust = math.ceil(availableTrust / 2)
        exploreTrust = math.floor(availableTrust / 2)

        self.setTrust(speedTrust, exploreTrust, 4, 2, 1, 0, 0)

    def __droneProductionIterator(self) -> None:
        """Self repeating function to create factories and drones after probe count has been able to increase for a while. It's main purpose is to quickly grow the swarm to create additional gifts."""
        if self.remainingDroneProductionIterations > 0 and self.threnodyCounter < 4:
            self.__setToCreatingDrones()

            # TODO: perhaps remove the multithreading, it's not really required if we just check timestamps in a loop
            TS.setTimer(10, self.__setToMatter)
            TS.setTimer(12, self.__setToCreatingProbes)  # Back to creating probes
            TS.setTimer(120, self.__droneProductionIterator)  # Repeat every two minutes

            self.remainingDroneProductionIterations -= 1
            TS.print(
                f"Performed next drone iteration, {self.remainingDroneProductionIterations} cycles remaining. Threnody counter at {self.threnodyCounter}.")

    def setTrust(self, speed: int, explore: int, replicate: int, hazard: int, factory: int, harvester: int, wire: int,
                 combat: int = 0) -> bool:
        """Set the new trust values. The values will first be decreased so enough trust is available for the remaining increases. Returns False if not enough trust is available."""
        mappedValues = {SettingType.Speed: speed, SettingType.Explore: explore, SettingType.Replicate: replicate,
                        SettingType.Hazard: hazard, SettingType.Factory: factory, SettingType.Harvester: harvester,
                        SettingType.Wire: wire, SettingType.Combat: combat}
        total = sum(mappedValues.values())

        if total > self.currTrust:
            return False

        with probeSettingMutex:
            currValues = self.settings.val()
            assert len(currValues) == len(mappedValues)

            # List together the type, newvalue and delta, sorted with most negative delta first
            deltaSets = [(type, newValue, newValue - currValues[type])
                         for type, newValue in mappedValues.items()]

            deltaSets.sort(key=lambda tuple: tuple[2])

            for type, newValue, _ in deltaSets:
                self.settings.set(type, newValue)

    def __init__(self, pageInfo: PageInfo, pageActions: PageActions) -> None:
        self.info = pageInfo
        self.actions = pageActions
        self.settings = ProbeSettings(pageActions)
        self.remainingDroneProductionIterations = 500  # pseudo-infinite

        self.fightingForHonor = False
        self.combatEnabled = False
        self.oodaLoopEnabled = False
        self.trustIncreased = False
        self.threnodyCounter = 0

        self.currTrust = 0
        self.yomiSpent = 0

        # Requires 351.658 yomi
        for _ in range(20):
            if self.actions.isEnabled("BuyProbeTrust"):
                self.yomiSpent += self.info.getInt("TrustCost")
                self.actions.pressButton("BuyProbeTrust")
                self.currTrust += 1

                TS.print(f"Bought {self.currTrust} Trust for a total of {self.yomiSpent} yomi.")
            else:
                break

        self.actions.setSlideValue("SwarmSlider", 199)  # We can manage for a long time without much production
        self.__setToCreatingProbes()  # Creating many probes is the first priority
        TS.setTimer(60, self.__droneProductionIterator)  # Start iterative cycle to increase drone count

        Listener.listenTo(Event.BuyProject, self.__combatBought, lambda project: project == "Combat", True)
        Listener.listenTo(Event.BuyProject, self.__oodaLoopBought, lambda project: project == "The OODA Loop", True)
        Listener.listenTo(Event.BuyProject, self.__namingTheBattles,
                          lambda project: project == "Name the battles", True)
        Listener.listenTo(Event.BuyProject, self.__threnodyBought,
                          lambda project: project == "Threnody for the Heroes", False)

    def increaseTrust(self) -> None:
        """Check if we can increase or buy additional trust and do so."""
        # TODO: This has no place here. Move somewhere else later.
        if self.actions.isEnabled("EntertainSwarm"):
            self.actions.pressButton("EntertainSwarm")

        if self.actions.isVisible("The OODA Loop"):
            # Save up the Yomi to buy The OODA loop first
            return

        if not self.trustIncreased and self.actions.isEnabled("IncreaseMaxTrust"):
            self.actions.pressButton("IncreaseMaxTrust")
            self.trustIncreased = True  # We only do this once

        if self.currTrust < 30 and self.actions.isEnabled("BuyProbeTrust"):
            self.yomiSpent += self.info.getInt("TrustCost")
            self.actions.pressButton("BuyProbeTrust")
            self.currTrust += 1

            TS.print(f"Bought {self.currTrust} Trust for a total of {self.yomiSpent} yomi.")

            # Some threadsafety, because timers could be running to change the probe settings
            self.__lockedCall(self.actions.pressButton, "RaiseReplication")

    def tick(self) -> None:
        # If available matter == 0 --> explore a bit
        self.increaseTrust()

        # TODO:
        # Determine the costs of Probe Trust 21-30
        # Once you hit nonillion amounts of probes you can shift to speed/exploration, can easily do a 6:6
        # You probably still need to convert all matter to clips, so make sure the are enough Drones before the endgame
        # Read the time from the message bar at the top of the page once you've converted the entire universe

# For reference:
# {"zero": -1, "million": 0, "billion": 1, "trillion": 2, "quadrillion": 3, "quintillion": 4, "sextillion": 5, "septillion": 6, "octillion": 7, "nonillion": 8, "decillion": 9}
