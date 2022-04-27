import time
from Util.Listener import Event, Listener
from Util.Resources.ThreadClicker import ThreadClicker
from Webpage.PageState.PageActions import PageActions
from Webpage.PageState.PageInfo import PageInfo
from Util.GameLoop.Phases.CurrentPhase import CurrentPhase, Phase
from Util.Resources.PhaseThree.ProbeTrustSettings import SettingType, ProbeTrustSettings
from Util.Timestamp import Timestamp as TS


class CombatWatcher():
    """Swaps the Probe Trust settings around while combat is inactive."""

    # After a battle has finished you have about 3 seconds before the next one makes contact.
    BATTLE_PEACE_TIME = 2.8

    def __init__(self, pageInfo: PageInfo, pageActions: PageActions, trust: int) -> None:
        """Instantiating this class assumes Combat, The OODA Loop and Name the battles have all been bought."""

        self.info = pageInfo
        self.actions = pageActions

        self.prevHonor = 0
        self.resetTime = 0.5  # Semi-random nonzero initial value
        self.trustSetter = ProbeTrustSettings(pageActions)
        self.availTrust = trust
        self.__enabled = True

        Listener.listenTo(Event.ButtonPressed, self.__increaseTrust, "BuyProbeTrust", False)

    def __increaseTrust(self, _: str) -> None:
        self.availTrust += 1

    def run(self):
        """Main loop. This is supposed to run on a seperate thread. Checks if the honor amount changes. If so, produce 
        drones for a short time."""

        while CurrentPhase.phase != Phase.End and self.__enabled:
            honor = self.info.getInt("honorDisplay")

            if honor != self.prevHonor:
                self.setPeaceTrust()
                self.prevHonor = honor

            time.sleep(0.1)

    def setPeaceTrust(self) -> None:
        """Swap trust settings around to optimize for non-noncombat for a short time."""

        funcTimestamp = TS.now()

        matterAcq = 1 if self.info.get("AvailMatter").text == "0" else 0
        replicate = self.availTrust - 2 * matterAcq - 9

        with ThreadClicker.Disabled():  # Maximize clicking efficiency
            self.setTrust(matterAcq, matterAcq, replicate, 6, 1, 1, 1, 0)  # No use for combat now

        setTime = TS.delta(funcTimestamp)
        sleepTime = CombatWatcher.BATTLE_PEACE_TIME - setTime - self.resetTime
        time.sleep(sleepTime)  # Now we're producing Drones
        TS.print(f"Producing drones for {sleepTime:.2f} seconds.")

        funcTimestamp = TS.now()
        with ThreadClicker.Disabled():
            self.setWarTrust()

        self.resetTime = CombatWatcher.BATTLE_PEACE_TIME - TS.delta(funcTimestamp)

    def setWarTrust(self) -> None:
        """Default trust settings to maximize probe production while engaging in combat with the drifters."""

        self.setTrust(2, 0, self.availTrust - 13, 6, 0, 0, 0, 5)

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

        currValues = self.trustSetter.val()
        assert len(currValues) == len(mappedValues)

        # List together the type, newvalue and delta, sorted with most negative delta first
        deltaSets = [(type, newValue, newValue - currValues[type])
                     for type, newValue in mappedValues.items()]

        deltaSets.sort(key=lambda tuple: tuple[2])

        for type, newValue, _ in deltaSets:
            self.trustSetter.set(type, newValue)

    def kill(self) -> None:
        """This kills the thread."""

        self.__enabled = False
