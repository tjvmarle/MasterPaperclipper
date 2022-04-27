from Util.Resources.OrderedEnum import OrderedEnum
from Util.Resources.PhaseThree.CombatWatcher import CombatWatcher
from Util.Resources.PhaseThree.ProbeTrustSettings import SettingType, ProbeTrustSettings
from Util.Resources.State import StateTracker
from Util.Resources.ThreadClicker import ThreadClicker
from Webpage.PageState.PageActions import PageActions
from Webpage.PageState.PageInfo import PageInfo
from Util.Timestamp import Timestamp as TS
from Util.Listener import Event, Listener

from multiprocessing.dummy import Process
import math


class ProbeBalancer():
    """Balances the trust settings for the probes. Also acquires new trust when possible."""

    class States(OrderedEnum):
        """Describes the different states this class goes through while progressing through phase 3."""
        NonCombat = 0
        CombatEnabled = 1
        SpeedyCombat = 2
        FightingForHonor = 3
        ExploringTheUniverse = 4

    def __init__(self, pageInfo: PageInfo, pageActions: PageActions) -> None:
        # TODO: Write base class with pageInfo, action, runnerlist and tick method.

        self.info = pageInfo
        self.actions = pageActions
        self.probeTrustSetter = ProbeTrustSettings(pageActions, 0)

        self.trustIncreased = False

        self.threnodyCounter = 0
        self.currTrust = 0

        self.lastIterationTime = TS.now()

        # TODO: Maybe put this in a Stateful base class
        self.currentState = StateTracker([enum for enum in ProbeBalancer.States])
        self.states = ProbeBalancer.States

        self.runners = [self.__increaseTrust, self.__checkAvailableMatter, self.__exploreUniverse]

        while self.actions.isEnabled("BuyProbeTrust"):
            self.actions.pressButton("BuyProbeTrust")
            self.currTrust += 1

        # We can manage for a long time without much production
        self.actions.setSlideValue("SwarmSlider", 190)
        self.__setToCreatingProbes()  # Creating many probes is the first priority

        Listener.listenTo(Event.BuyProject, self.__combatBought, "Combat", True)
        Listener.listenTo(Event.BuyProject, self.__oodaLoopBought, "The OODA Loop", True)
        Listener.listenTo(Event.BuyProject, self.__namingTheBattles, "Name the battles", True)
        Listener.listenTo(Event.BuyProject, self.__threnodyBought, "Threnody for the Heroes", False)

    def __increaseTrust(self) -> None:
        """Check if we can increase or buy additional trust and do so."""

        if self.actions.isVisible("The OODA Loop"):
            # Save up the Yomi to buy The OODA loop first
            return

        # TODO: This method can probably be moved to a seperate class
        if not self.trustIncreased and self.actions.isEnabled("IncreaseMaxTrust"):
            self.actions.pressButton("IncreaseMaxTrust")
            self.trustIncreased = True  # We only do this once

        if self.currTrust < 30 and self.actions.isEnabled("BuyProbeTrust"):
            self.actions.pressButton("BuyProbeTrust")
            self.currTrust += 1
            self.actions.pressButton("RaiseReplication")

    def __checkAvailableMatter(self) -> None:
        """Checks if Probe Trust settings needs to be changed to explore for additional matter."""

        # TODO: Trigger this when Matter and Wire are 0 and Unused clips has descreased x% in y seconds.
        if TS.delta(self.lastIterationTime) < 10.0 or self.info.get("AvailMatter").text != 0:
            return

        TS.print("Acquire Matter!")

        availableTrust = self.currTrust - 7
        speedTrust = math.ceil(availableTrust / 2)
        exploreTrust = math.floor(availableTrust / 2)

        self.probeTrustSetter.setTrust(speedTrust, exploreTrust, 4, 2, 1, 0, 0)
        TS.setTimer(5, "MatterAcquisition", self.__setToCreatingProbes)
        self.lastIterationTime = TS.now()

    def __exploreUniverse(self) -> None:
        """Checks if enough Probes have been generated and triggers exploration of the entire universe."""

        if self.currentState == self.states.FightingForHonor and "nonillion" in self.info.get("LaunchedProbes").text:
            TS.print("Trigger exploring the universe.")
            self.currentState.goTo(self.states.ExploringTheUniverse)
            self.combatWatcher.kill()

            # Delay a bit to build up more probes
            TS.setTimer(60, "SetTrust", self.probeTrustSetter.setTrust, 4, 4, 12, 6, 0, 0, 0, 4)

    def __setToCreatingProbes(self) -> None:
        """Change probe settings to produce as many probes as possible. This is more or less the default setting."""
        speed = 2 if self.currentState.atLeast(self.states.SpeedyCombat) else 0

        if self.currentState.atLeast(self.states.CombatEnabled):
            self.probeTrustSetter.setTrust(speed, 0, self.currTrust - speed - 11, 6, 0, 0, 0, 5)
        else:
            self.probeTrustSetter.setTrust(0, 0, self.currTrust - 6, 6, 0, 0, 0)

    def __namingTheBattles(self, _: str) -> None:
        self.combatWatcher = CombatWatcher(self.info, self.actions, self.currTrust)
        Process(target=self.combatWatcher.run, args=[], name="CombatWatcher").start()
        self.runners.remove(self.__checkAvailableMatter)  # Will now be handled by the CombatWatcher

    def __combatBought(self, _: str) -> None:
        self.currentState.goTo(self.states.CombatEnabled)

    def __oodaLoopBought(self, _: str) -> None:
        self.currentState.goTo(self.states.SpeedyCombat)

    def __threnodyBought(self, _: str) -> None:
        self.threnodyCounter += 1
        if self.threnodyCounter == 4:
            self.actions.setSlideValue("SwarmSlider", 10)
            ThreadClicker.disable()  # Don't need this anymore

    def tick(self) -> None:

        for func in self.runners:
            func()
