from functools import partial
from typing import Callable, List
from Util.Resources.StatefulRunner import StatefulRunner
from Util.Resources.OrderedEnum import OrderedEnum
from Util.Resources.PhaseThree.CombatWatcher import CombatWatcher
from Util.Resources.PhaseThree.ProbeTrustSettings import ProbeTrustSettings
from Util.Resources.ThreadClicker import ThreadClicker
from Webpage.PageState.PageActions import PageActions
from Webpage.PageState.PageInfo import PageInfo
from Util.Timestamp import Timestamp as TS
from Util.Listener import Event, Listener

from multiprocessing.dummy import Process
from datetime import timedelta


class ProbeBalancer(StatefulRunner):
    """Balances the trust settings for the probes. Also acquires new trust when possible."""

    class States(OrderedEnum):
        """Describes the different states this class goes through while progressing through phase 3."""
        NonCombat = 0
        CombatEnabled = 1
        SpeedyCombat = 2
        FightingForHonor = 3
        ExploringTheUniverse = 4

    def __init__(self, pageInfo: PageInfo, pageActions: PageActions) -> None:
        super().__init__(pageInfo, pageActions, ProbeBalancer.States)
        self.states: ProbeBalancer.States

        self.probeTrustSetter = ProbeTrustSettings(pageInfo, pageActions, 0)
        self.threnodyCounter = 0
        self.currTrust = 0

        self.lastResourceAcquisition = TS.now()
        self.loopCounter = 10

        self.runners = [self.__increaseMaxTrust, self.__buyTrust, self.__acquireAdditionalResources]

        while self.actions.isEnabled("BuyProbeTrust"):
            self.actions.pressButton("BuyProbeTrust")
            self.currTrust += 1

        # We can manage for a long time without much production
        self.actions.setSlideValue("SwarmSlider", 190)

        Listener.listenTo(Event.BuyProject, self.__combatBought, "Combat", True)
        Listener.listenTo(Event.BuyProject, self.__oodaLoopBought, "The OODA Loop", True)
        Listener.listenTo(Event.BuyProject, self.__nameTheBattlesBought, "Name the battles", True)
        Listener.listenTo(Event.BuyProject, self.__threnodyBought, "Threnody for the Heroes", False)

    def __increaseMaxTrust(self) -> None:
        """Check if we can increase our max Trust and do so."""

        # We only do this once, the game should be finished before another upgrade would become available.
        if self.actions.isEnabled("IncreaseMaxTrust"):
            self.actions.pressButton("IncreaseMaxTrust")
            self.runners.remove(self.__increaseMaxTrust)

    def __buyTrust(self) -> None:
        """Check if we can buy additional trust and do so."""

        if self.actions.isVisible("The OODA Loop"):
            # Save up the Yomi to buy The OODA loop first
            return

        if self.currTrust < 30 and self.actions.isEnabled("BuyProbeTrust"):
            self.actions.pressButton("BuyProbeTrust")
            self.currTrust += 1

    def __acquireAdditionalResources(self) -> None:
        """Checks if we can increase drone or factory count and/or acquire more matter for a short while. This will 
        later be replaced by the CombatWatcher."""

        if TS.delta(self.lastResourceAcquisition) < 15.0 and self.currentState.before(self.states.FightingForHonor):
            return

        combatVal = 0 if self.currentState.before(self.states.CombatEnabled) else 5
        replicationTrust = self.currTrust - 7 - combatVal
        # FIXME: If OODA loop has been bought, speed should remain at 2
        trustRunners: List[Callable] = []
        if self.loopCounter == 20:
            # Only produce factories from time to time
            trustRunners.append(partial(self.probeTrustSetter.setTrust, 0, 0, replicationTrust, 6, 1, 0, 0, combatVal))
            self.loopCounter = 0
        self.loopCounter += 1

        trustRunners.append(partial(self.probeTrustSetter.setTrust, 0, 0, replicationTrust, 6, 0, 1, 0, combatVal))
        trustRunners.append(partial(self.probeTrustSetter.setTrust, 0, 0, replicationTrust, 6, 0, 0, 1, combatVal))

        if self.info.get("AvailMatter").text == "0":
            trustRunners.append(partial(self.probeTrustSetter.setTrust, 1, 1,
                                        replicationTrust - 1, 6, 0, 0, 0, combatVal))

        trustRunners.append(self.__setToCreatingProbes)

        # Run each trust setting for the same amount of time
        for count, runner in enumerate(trustRunners):
            TS.setTimer(count, "DroneAcquisition", runner)

        self.lastResourceAcquisition = TS.now()

    def __exploreUniverse(self) -> None:
        """Checks if enough Probes have been generated and triggers exploration of the entire universe."""

        # FIXME: Somehow this didn't trigger.
        text = self.info.get("LaunchedProbes").text
        sizeNonillion = ("nonillion" in text)
        if self.currentState == self.states.FightingForHonor and sizeNonillion:
            TS.print("Trigger exploring the universe.")
            self.currentState.goTo(self.states.ExploringTheUniverse)
            self.combatWatcher.kill()

            # Delay a bit to build up more probes
            TS.setTimer(60, "SetTrust", self.probeTrustSetter.setTrust, 4, 4, self.currTrust - 18, 6, 0, 0, 0, 4)
            self.runners.remove(self.__exploreUniverse)

    def __setToCreatingProbes(self) -> None:
        """Change probe settings to produce as many probes as possible. This is more or less the default setting."""
        speed = 2 if self.currentState.atLeast(self.states.SpeedyCombat) else 0

        if self.currentState.atLeast(self.states.CombatEnabled):
            self.probeTrustSetter.setTrust(speed, 0, self.currTrust - speed - 11, 6, 0, 0, 0, 5)
        else:
            self.probeTrustSetter.setTrust(0, 0, self.currTrust - 6, 6, 0, 0, 0)

    def __combatBought(self, _: str) -> None:
        self.currentState.goTo(self.states.CombatEnabled)
        self.__setToCreatingProbes()  # Updates Trust points allocated to Combat

    def __oodaLoopBought(self, _: str) -> None:
        self.currentState.goTo(self.states.SpeedyCombat)
        self.__setToCreatingProbes()  # Updates probe speed

    def __nameTheBattlesBought(self, _: str) -> None:
        self.runners.remove(self.__acquireAdditionalResources)  # Will now be handled by the CombatWatcher
        self.runners.remove(self.__buyTrust)                    # Same
        self.runners.append(self.__exploreUniverse)
        self.currentState.goTo(self.states.FightingForHonor)

        # Manage the trust settings from a seperate thread now. This will optimize trust settings in between the
        # battles by swapping the combat/speed points around.
        self.combatWatcher = CombatWatcher(self.info, self.actions, self.currTrust)
        Process(target=self.combatWatcher.run, args=[], name="CombatWatcher").start()

    def __threnodyBought(self, _: str) -> None:
        self.threnodyCounter += 1
        if self.threnodyCounter == 4:
            self.actions.setSlideValue("SwarmSlider", 10)
            ThreadClicker.disable()  # Don't need this anymore
