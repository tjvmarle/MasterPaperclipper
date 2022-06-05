from functools import partial
import math
import time
from Util.Listener import Event, Listener
from Util.Resources.ThreadClicker import ThreadClicker
from Util.Resources.StatefulRunner import StatefulRunner
from Util.Resources.OrderedEnum import OrderedEnum
from Webpage.PageState.PageActions import PageActions
from Webpage.PageState.PageInfo import PageInfo
from Util.GameLoop.Phases.CurrentPhase import CurrentPhase, Phase
from Util.Resources.PhaseThree.ProbeTrustSettings import SettingType, ProbeTrustSettings
from Util.Timestamp import Timestamp as TS

from typing import List


class CombatWatcher(StatefulRunner):
    """Swaps the Probe Trust settings around while combat is inactive."""

    class States(OrderedEnum):
        """Describes the different states this class goes through while progressing through phase 3."""
        Growth = 0          # Maximize increasing both probes and drones
        Replication = 1     # Only maximize probe count
        Exploration = 2     # Maximize exploration

    # After a battle has finished you have about 3 seconds before the next one makes contact.
    BATTLE_PEACE_TIME = 3.0

    def __init__(self, pageInfo: PageInfo, pageActions: PageActions, trust: int) -> None:
        """Instantiating this class assumes Combat, The OODA Loop and Name the battles have all been bought."""
        super().__init__(pageInfo, pageActions, CombatWatcher.States)
        self.states: CombatWatcher.States

        self.prevHonor = 0
        self.resetTime = 0.5  # Semi-random nonzero initial value
        self.probeTrustSetter = ProbeTrustSettings(pageInfo, pageActions, trust)
        self.availTrust = trust
        self.__enabled = True
        self.droneProductionRatio = 5

        Listener.listenTo(Event.ButtonPressed, self.__increaseTrust, "BuyProbeTrust", False)
        Listener.listenTo(Event.BuyProject, self.__goToWrapper, "Strategic Attachment", True)

    def __goToWrapper(self, _: str):
        """After acquiring strategic Attachment there's no more need for more drones."""
        TS.print("Switching CombatWatcher to Replication")
        self.currentState.goTo(self.states.Replication)

    def __increaseTrust(self, _: str) -> None:
        self.availTrust += 1
        # self.probeTrustSetter.sync()  # TODO: Probably still not enough as long as ProbeBalancer keeps buying Trust.

    def run(self):
        """Main loop. This is supposed to run on a seperate thread. Checks if the honor amount changes. If so, produce 
        drones for a short time."""

        loopCounter = 10
        while CurrentPhase.phase != Phase.End and self.__enabled:
            honor = self.info.getInt("Honor")

            if honor != self.prevHonor:
                self.__setPeaceTrust()
                self.prevHonor = honor

            if self.currentState.get() == self.states.Replication:

                # Occasionally check if we should move to the exploration phase.
                loopCounter -= 1
                if loopCounter == 0:
                    loopCounter = 10
                    # TODO: Perhaps move the 'octillion'-trigger to the config.
                    if "octillion" in self.info.get("LaunchedProbes").text:
                        TS.print("Switching CombatWatcher to Exploration")
                        self.currentState.goTo(self.states.Exploration)

            # Taken over from ProbeBalancer to prevent race conditions.
            if self.availTrust < 30 and self.actions.isEnabled("BuyProbeTrust"):
                self.actions.pressButton("BuyProbeTrust")

            time.sleep(0.1)

        TS.print("Combatwatcher terminated.")

    def __setPeaceTrust(self) -> None:
        """Swap trust settings around to optimize for noncombat for a short time."""

        funcTimestamp = TS.now()

        # OPT: Base matter acquisition on Unused clips going down, not on available matter.
        # OPT: At a certain probe count there's no need anymore for additional Drones/Factories. Focus more on
        # replication from that point.
        # matterAcq = 1 if self.info.get("AvailMatter").text == "0" else 0
        # replicate = self.availTrust - 2 * matterAcq - 9

        trustList = self.__getPeaceTrustList()

        with ThreadClicker.Disabled():  # Maximize clicking efficiency
            self.probeTrustSetter.setTrust(*trustList)

        setTime = TS.delta(funcTimestamp)
        sleepTime = max(CombatWatcher.BATTLE_PEACE_TIME - setTime - self.resetTime, 0)
        time.sleep(sleepTime)  # Now we're producing Drones

        funcTimestamp = TS.now()
        with ThreadClicker.Disabled():
            self.__setWarTrust()

        self.resetTime = TS.delta(funcTimestamp)

    def __getPeaceTrustList(self) -> List[int]:
        """Gives a list of Trust settings depending on current state."""

        # OPT: You don't need that many factories
        # OPT: Try to maintain the same ratio of Harvesters:Wire as in Phase 2
        # OPT: Only explore once Unused clips starts dropping
        # Put all leftover points in replication
        matterAcq = 1 if self.info.get("AvailMatter").text == "0" else 0

        if self.currentState.get() == self.states.Growth:
            replicate = self.availTrust - 2 * matterAcq - 9
            return [matterAcq, matterAcq, replicate, 6, 1, 1, 1, 0]

        elif self.currentState.get() == self.states.Replication:

            # Still create drones, but with lower frequency. Otherwise we'll stay way too low.
            self.droneProductionRatio -= 1
            droneNr = 0
            if self.droneProductionRatio == 0:
                self.droneProductionRatio = 5
                droneNr = 1

            replicate = self.availTrust - 2 * matterAcq - 6 - 3 * droneNr
            return [matterAcq, matterAcq, replicate, 6, droneNr, droneNr, droneNr, 0]

        elif self.currentState.get() == self.states.Exploration:
            explore = math.floor((self.availTrust - 20) / 2)
            return [math.floor(explore), math.ceil(explore), 14, 6, 0, 0, 0, 0]

    def __setWarTrust(self) -> None:
        """Default trust settings to maximize probe production while engaging in combat with the drifters."""
        # OPT: Once the ratio of probes:drifters is large enough, 1 speed might suffice.
        self.probeTrustSetter.setTrust(2, 0, self.availTrust - 13, 6, 0, 0, 0, 5)

    def kill(self) -> None:
        """This kills the thread."""

        TS.print("Killing the Combatwatcher.")
        self.__enabled = False
