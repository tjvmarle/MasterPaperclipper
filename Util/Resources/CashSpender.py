# Responsible for spending money on wire, clippers and marketing
from multiprocessing.dummy import Process
from Util.Files.Config import Config

from Util.Listener import Event, Listener
from Util.Resources.HedgeFunder import HedgeFunder
from Util.Resources.PriceWatcher import PriceWatcher
from Webpage.PageState.PageActions import PageActions
from Webpage.PageState.PageInfo import PageInfo
from Util.Timestamp import Timestamp as TS


class CashSpender():
    def __kill(self, _: str) -> None:
        TS.print(f"Hypnodrones released, killing of CashSpender.")
        self.alive = False

    def __init__(self, pageInfo: PageInfo, pageActions: PageActions) -> None:
        self.info = pageInfo
        self.actions = pageActions

        self.highestWireCost = 27
        self.clipperSpeed = 2.5
        self.megaPerformance = 1
        self.nextClipper = "BuyAutoclipper"
        self.killWire = False
        self.pricer = PriceWatcher(self.info, self.actions)
        self.runners = [self.pricer]
        self.hedgeInits = 2
        self.clippersAvailable = False
        self.buyKilled = False
        self.alive = True
        self.trustVisible = False

        Listener.listenTo(Event.BuyProject, self.wireBuyerAcquired, lambda project: project == "WireBuyer", True)
        Listener.listenTo(Event.BuyProject, self.revTrackerAcquired, lambda project: project == "RevTracker", True)
        Listener.listenTo(Event.BuyProject, self.algoTradingAcquired,
                          lambda project: project == "Algorithmic Trading", True)
        Listener.listenTo(Event.BuyProject, self.__kill, lambda project: project == "Release the Hypnodrones", True)

        filter = lambda x: x in ("Hadwiger Clip Diagrams", "Improved MegaClippers",
                                 "Even Better MegaClippers", "Optimized MegaClippers")
        Listener.listenTo(Event.BuyProject, self.clipperImprovementAcquired, filter, False)

    def clipperImprovementAcquired(self, project: str) -> None:
        TS.print(f"Clipper improvement acquired: {project}.")
        if project == "Hadwiger Clip Diagrams":
            self.clipperSpeed += 5
        elif project == "Improved MegaClippers":
            self.megaPerformance += 0.25
        elif project == "Even Better MegaClippers":
            self.megaPerformance += 0.50
        elif project == "Optimized MegaClippers":
            self.megaPerformance += 1.00

    def wireBuyerAcquired(self, _: str) -> None:
        self.killWire = True

    def checkHedgeInits(self) -> None:
        # UGLY: but saves a bunch of additional code
        if self.hedgeInits == 0:
            self.runners.append(HedgeFunder(self.info, self.actions))

    def revTrackerAcquired(self, _: str) -> None:
        thread = Process(target=self.pricer.activateRevTracker)
        thread.start()
        self.hedgeInits -= 1
        self.checkHedgeInits()

    def algoTradingAcquired(self, _: str) -> None:
        self.hedgeInits -= 1
        self.checkHedgeInits()

    def getCallback(self):
        return self.projectAcquired

    def __determineClipper(self) -> float:
        # Check which clipper to buy next
        if not self.actions.isVisible("BuyMegaClipper"):
            return self.info.getFl("AutoCost")

        autoPrice, megaPrice = [self.info.getFl(clipCost) for clipCost in ("AutoCost", "MegaCost")]
        buyAuto = autoPrice / self.clipperSpeed < megaPrice / (self.megaPerformance * 500)
        self.nextClipper = "BuyAutoclipper" if buyAuto else "BuyMegaClipper"
        return autoPrice if buyAuto else megaPrice

    def __buyClippersOrMarketing(self):
        if not self.clippersAvailable:
            # You can't buy clippers untill you've made $5
            self.clippersAvailable = self.actions.isVisible("BuyAutoclipper")
            return

        if self.buyKilled:
            return

        if not self.trustVisible:
            # Optimization - reducing amount of calls to the driver
            self.trustVisible = self.info.isVisible("Trust")

        if self.info.getInt("TotalClips") > 122_000_000:
            TS.print(f"Reached 122M clips in {TS.deltaStr(Config.get('Gamestart'))}, killing of Clipper acquisition.")
            self.buyKilled = True  # Kills of this method
            return

        # Occasionally buy some marketing instead
        # FIXME: Only save up for marketing if the cost can be achieved within the timeframe before investing starts
        lvlUpCost = self.info.getFl("MarketingCost")
        clipperCost = self.__determineClipper()
        funds = self.info.getFl("Funds")

        # TODO: Move this ratio to Config.
        buyMarketing = lvlUpCost < 4 * clipperCost
        if buyMarketing and funds > self.highestWireCost + lvlUpCost:
            self.actions.pressButton("LevelUpMarketing")
        elif buyMarketing:
            return

        if (funds - self.highestWireCost) > clipperCost:
            self.actions.pressButton(self.nextClipper)

    def __updateWire(self):
        if self.killWire:
            return

        wireCost = self.info.getInt("WireCost")
        self.highestWireCost = max(wireCost, self.highestWireCost)

        if self.info.getFl("Funds") < wireCost:
            return

        wire = self.info.getInt("Wire")
        if wire < 500 or (
                wire < 1500 and wireCost / self.highestWireCost <= 0.65) or (
                wire < 2500 and wireCost / self.highestWireCost <= 0.50):  # Either buy when low or cheap
            self.actions.pressButton("BuyWire")

    def tick(self):
        if not self.alive:
            return

        self.__updateWire()
        self.__buyClippersOrMarketing()
        for runner in self.runners:
            runner.tick()
