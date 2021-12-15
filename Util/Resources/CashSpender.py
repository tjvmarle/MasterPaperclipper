# Responsible for spending money on wire, clippers and marketing
from multiprocessing.dummy import Process
from Util.AcquisitionHandler import AcquisitionHandler
from Util.Files.Config import Config

from Util.Resources.HedgeFunder import HedgeFunder
from Util.Resources.PriceWatcher import PriceWatcher
from Webpage.PageState.PageActions import PageActions
from Webpage.PageState.PageInfo import PageInfo
from Util.Timestamp import Timestamp as TS


class CashSpender():
    def clipperImprovementAcquired(self, project: str) -> None:
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

    def __init__(self, pageInfo: PageInfo, pageActions: PageActions) -> None:
        self.info = pageInfo
        self.actions = pageActions
        self.highestWireCost = 27
        self.clipperSpeed = 2.5  # Includes most of the upgrades
        self.megaPerformance = 1
        self.nextClipper = "BuyAutoclipper"
        self.killWire = False
        self.pricer = PriceWatcher(self.info, self.actions)
        self.runners = [self.pricer]
        self.hedgeInits = 2
        self.projectWatcher = AcquisitionHandler()
        self.clippersAvailable = False
        self.maxTrustReached = False

        # If only this language would have useful lambda's
        self.projectWatcher.addHandle("WireBuyer", self.wireBuyerAcquired)
        self.projectWatcher.addHandle("RevTracker", self.revTrackerAcquired)
        self.projectWatcher.addHandle("Algorithmic Trading", self.algoTradingAcquired)
        for project in ("Hadwiger Clip Diagrams", "Improved MegaClippers", "Even Better MegaClippers",
                        "Optimized MegaClippers"):
            self.projectWatcher.addHandle(project, self.clipperImprovementAcquired)

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

    def __buy(self):
        if not self.clippersAvailable:
            # You can't buy clippers untill you've made $5
            self.clippersAvailable = self.actions.isVisible("BuyAutoclipper")
            return

        if self.maxTrustReached:
            return

        if self.info.getInt("Trust") >= 90:
            TS.print(f"Reached 90 trust in {TS.delta(Config.get('Gamestart'))}, killing of Clipper acquisition.")
            self.maxTrustReached = True

        # Occasionally buy some marketing instead
        lvlUpCost = self.info.getFl("MarketingCost")
        clipperCost = self.__determineClipper()
        funds = self.info.getFl("Funds")

        buyMarketing = lvlUpCost < 3 * clipperCost
        if buyMarketing and funds > self.highestWireCost + lvlUpCost:
            self.actions.pressButton("LevelUpMarketing")

        if not buyMarketing and (funds - self.highestWireCost) > clipperCost:
            self.actions.pressButton(self.nextClipper)
            self.info.update("Funds")

    def __updateWire(self):
        if self.killWire:
            return

        wireCost = self.info.getInt("WireCost")
        self.highestWireCost = max(wireCost, self.highestWireCost)

        if self.info.getFl("Funds") < wireCost:
            return

        wire = self.info.getInt("Wire")
        if wire < 200 or (
                wire < 1500 and wireCost / self.highestWireCost <= 0.6) or (
                wire < 2500 and wireCost / self.highestWireCost <= 0.45):  # Either buy when low or cheap
            self.actions.pressButton("BuyWire")
            self.info.update("Funds")

    def tick(self):
        self.__updateWire()
        self.__buy()
        for runner in self.runners:
            runner.tick()
