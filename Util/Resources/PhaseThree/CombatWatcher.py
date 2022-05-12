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
    BATTLE_PEACE_TIME = 3.0

    def __init__(self, pageInfo: PageInfo, pageActions: PageActions, trust: int) -> None:
        """Instantiating this class assumes Combat, The OODA Loop and Name the battles have all been bought."""

        self.info = pageInfo
        self.actions = pageActions

        self.prevHonor = 0
        self.resetTime = 0.5  # Semi-random nonzero initial value
        self.probeTrustSetter = ProbeTrustSettings(pageActions, trust)
        self.availTrust = trust
        self.__enabled = True

        Listener.listenTo(Event.ButtonPressed, self.__increaseTrust, "BuyProbeTrust", False)

    def __increaseTrust(self, _: str) -> None:
        self.availTrust += 1

    def run(self):
        """Main loop. This is supposed to run on a seperate thread. Checks if the honor amount changes. If so, produce 
        drones for a short time."""

        while CurrentPhase.phase != Phase.End and self.__enabled:
            honor = self.info.getInt("Honor")

            if honor != self.prevHonor:
                self.__setPeaceTrust()
                self.prevHonor = honor

            time.sleep(0.1)

    def __setPeaceTrust(self) -> None:
        """Swap trust settings around to optimize for noncombat for a short time."""

        funcTimestamp = TS.now()

        # OPT: Base matter acquisition on Unused clips going down, not on available matter.
        # OPT: At a certain probe count there's no need anymore for additional Drones/Factories. Focus more on
        # replication from that point.
        matterAcq = 1 if self.info.get("AvailMatter").text == "0" else 0
        replicate = self.availTrust - 2 * matterAcq - 9

        with ThreadClicker.Disabled():  # Maximize clicking efficiency
            self.probeTrustSetter.setTrust(matterAcq, matterAcq, replicate, 6, 1, 1, 1, 0)  # No use for combat now

        setTime = TS.delta(funcTimestamp)
        sleepTime = max(CombatWatcher.BATTLE_PEACE_TIME - setTime - self.resetTime, 0)
        time.sleep(sleepTime)  # Now we're producing Drones

        funcTimestamp = TS.now()
        with ThreadClicker.Disabled():
            self.__setWarTrust()

        self.resetTime = TS.delta(funcTimestamp)

    def __setWarTrust(self) -> None:
        """Default trust settings to maximize probe production while engaging in combat with the drifters."""

        self.probeTrustSetter.setTrust(2, 0, self.availTrust - 13, 6, 0, 0, 0, 5)

    def kill(self) -> None:
        """This kills the thread."""

        self.__enabled = False
