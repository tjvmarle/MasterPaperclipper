from Util.Resources.PhaseThree.ProbeTrustSettings import SettingType, ProbeTrustSettings
from Webpage.PageState.PageActions import PageActions
from Webpage.PageState.PageInfo import PageInfo
from Util.Timestamp import Timestamp as TS
from Util.Listener import Event, Listener

from multiprocessing import Lock
import math


# Some added safety since we're working with seperate, timed threads
probeSettingMutex = Lock()


class ProbeBalancer():
    """Balances the trust settings for the probes. Also acquires new trust when possible."""

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
        if self.threnodyCounter == 4:
            self.actions.setSlideValue("SwarmSlider", 10)
            self.actions.setThreadClickerActivity(
                False)  # Don't need this anymore

    def __setToCreatingDrones(self) -> None:
        """Change probe settings to produce a large amount of drones. Usually done intermittently to quickly increase swarm power."""
        speed = 2 if self.oodaLoopEnabled else 0
        self.setTrust(speed, 0, self.currTrust - speed - 8, 6, 0, 1, 1)

    def __setToCreatingProbes(self) -> None:
        """Change probe settings to produce as many probes as possible. This is more or less the default setting."""
        speed = 2 if self.oodaLoopEnabled else 0

        # OPT: Perhaps don't enable combat until Name the battles has been enabled --> you want to lose probes
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
            TS.print(
                f"Skipping matter, current available matter is {matter} g.")
            return
        TS.print("Acquiring matter.")

        availableTrust = self.currTrust - 7
        speedTrust = math.ceil(availableTrust / 2)
        exploreTrust = math.floor(availableTrust / 2)

        self.setTrust(speedTrust, exploreTrust, 4, 2, 1, 0, 0)

    def acquireMatter(self) -> None:
        matterAcquisitionTime = 5
        secondsSinceLastIteration = int(TS.delta(self.lastIterationTime))

        if secondsSinceLastIteration < 11:
            # We might be creating drones now
            return

        if self.nextIteration - secondsSinceLastIteration < matterAcquisitionTime and self.remainingDroneProductionIterations == 0:
            # Matter acquisition could be cut short by the next iteration triggering
            return

        if not self.actions.isEnabled("LaunchProbe") and self.remainingDroneProductionIterations != 0:
            # TODO: Perhaps trigger this when Matter and Wire are 0 and Unused clips has descreased x% in y seconds.
            # FIXME: This should not trigger again if a thread is already running.
            TS.print("Acquire Matter!")
            self.__setToMatter()
            TS.setTimer(matterAcquisitionTime, "MatterAcquisition", self.__setToCreatingProbes)

    def __droneProductionIterator(self) -> None:
        """Self repeating function to create factories and drones after probe count has been able to increase for a while. It's main purpose is to quickly grow the swarm to create additional gifts."""
        if self.remainingDroneProductionIterations == 0:
            return

        self.nextIteration = 120 + 30 * self.threnodyCounter

        self.lastIterationTime = TS.now()
        if self.remainingDroneProductionIterations > 0:
            self.__setToCreatingDrones()
        TS.print("Triggering next iteration of Drone Production.")

        TS.setTimer(10, "ProbeCreation", self.__setToCreatingProbes)
        TS.setTimer(self.nextIteration, "DroneProductionIterator", self.__droneProductionIterator)

        self.remainingDroneProductionIterations -= 1
        TS.print(
            f"Performed next drone iteration, {self.remainingDroneProductionIterations} cycles remaining. Threnody counter at {self.threnodyCounter}.")

    def exploreUniverse(self) -> None:
        # Only execute the setTimer once, change the remainingDrProdIt to something nicer
        if "nonillion" in self.info.get("LaunchedProbes").text and self.remainingDroneProductionIterations != 0:
            probeSettingMutex.acquire()
            TS.print("Start exploring the universe.")
            self.remainingDroneProductionIterations = 0  # Hacky, but fine for now.
            # Delay a bit to build up more probes
            TS.setTimer(60, "SetTrust", self.setTrust, 2, 2, 16, 6, 0, 0, 0, 4)
            probeSettingMutex.release()

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
        self.settings = ProbeTrustSettings(pageActions)
        self.remainingDroneProductionIterations = 500  # pseudo-infinite

        self.fightingForHonor = False
        self.combatEnabled = False
        self.oodaLoopEnabled = False
        self.trustIncreased = False
        self.threnodyCounter = 0

        self.currTrust = 0
        self.yomiSpent = 0

        self.nextIteration = 120
        self.lastIterationTime = TS.now()

        # Requires 351.658 yomi
        for _ in range(20):
            if self.actions.isEnabled("BuyProbeTrust"):
                self.yomiSpent += self.info.getInt("TrustCost")
                self.actions.pressButton("BuyProbeTrust")
                self.currTrust += 1

                TS.print(
                    f"Bought {self.currTrust} Trust for a total of {self.yomiSpent} yomi.")
            else:
                break

        # We can manage for a long time without much production
        self.actions.setSlideValue("SwarmSlider", 190)
        self.__setToCreatingProbes()  # Creating many probes is the first priority
        # Start iterative cycle to increase drone count
        TS.setTimer(60, "DroneProductionIterator", self.__droneProductionIterator)

        Listener.listenTo(Event.BuyProject, self.__combatBought,
                          lambda project: project == "Combat", True)
        Listener.listenTo(Event.BuyProject, self.__oodaLoopBought,
                          lambda project: project == "The OODA Loop", True)
        Listener.listenTo(Event.BuyProject, self.__namingTheBattles,
                          lambda project: project == "Name the battles", True)
        Listener.listenTo(Event.BuyProject, self.__threnodyBought,
                          lambda project: project == "Threnody for the Heroes", False)

    def increaseTrust(self) -> None:
        """Check if we can increase or buy additional trust and do so."""
        # TODO: This has no place here. Move somewhere else later.
        if self.actions.isEnabled("EntertainSwarm"):
            self.actions.pressButton("EntertainSwarm")

        if self.actions.isEnabled("SynchronizeSwarm"):
            self.actions.pressButton("SynchronizeSwarm")

        if self.actions.isVisible("The OODA Loop"):
            # Save up the Yomi to buy The OODA loop first
            return

        # TODO: This method can probably be moved to a seperate class
        if not self.trustIncreased and self.actions.isEnabled("IncreaseMaxTrust"):
            self.actions.pressButton("IncreaseMaxTrust")
            self.trustIncreased = True  # We only do this once

        if self.currTrust < 30 and self.actions.isEnabled("BuyProbeTrust"):
            self.yomiSpent += self.info.getInt("TrustCost")
            self.actions.pressButton("BuyProbeTrust")
            self.currTrust += 1

            TS.print(
                f"Bought {self.currTrust} Trust for a total of {self.yomiSpent} yomi.")

            # Some threadsafety, because timers could be running to change the probe settings
            self.__lockedCall(self.actions.pressButton, "RaiseReplication")

    def tick(self) -> None:
        self.increaseTrust()
        self.acquireMatter()
        self.exploreUniverse()

        # TODO:
        # Determine the costs of Probe Trust 21-30
        # Once you hit nonillion amounts of probes you can shift to speed/exploration, can easily do a 6:6
        # You probably still need to convert all matter to clips, so make sure the are enough Drones before the endgame
        # Read the time from the message bar at the top of the page once you've converted the entire universe

# For reference:
# {"zero": -1, "million": 0, "billion": 1, "trillion": 2, "quadrillion": 3, "quintillion": 4, "sextillion": 5, "septillion": 6, "octillion": 7, "nonillion": 8, "decillion": 9}
# 937947 yomi for 30 Probe Trust
# Last run: 1:58:56
