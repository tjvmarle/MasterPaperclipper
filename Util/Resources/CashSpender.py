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

    def __moneyWithdrawn(self, _: str) -> None:
        funds = self.info.getFl("Funds")
        TS.print(f"Money withdrawn from bank, current cash is {funds}.")
        self.buyingOutGoodwill = (funds > 511_500_000.0) and self.tokensOfGoodwill > 0

    def __tokensBought(self, _: str) -> None:
        self.tokensOfGoodwill -= 1
        if self.tokensOfGoodwill == 0:
            self.buyingOutGoodwill = False

    def __init__(self, pageInfo: PageInfo, pageActions: PageActions) -> None:
        self.info = pageInfo
        self.actions = pageActions

        self.highestWireCost = 27
        self.clipperSpeed = 2.5
        self.megaPerformance = 1
        self.nextObjective = None
        self.killWire = False
        self.pricer = PriceWatcher(self.info, self.actions)
        self.runners = [self.pricer]
        self.hedgeInits = 2
        self.clippersAvailable = False
        self.buyKilled = False
        self.alive = True
        self.enoughClippers = False
        self.noMegas = True
        self.marketingLevel = 1
        self.tokensOfGoodwill = Config.get("phaseOneProjects").count("Another Token of Goodwill")
        self.buyingOutGoodwill = False

        # UGLY: this class probably needs some splitting up
        Listener.listenTo(Event.BuyProject, self.__wireBuyerAcquired, lambda project: project == "WireBuyer", True)
        Listener.listenTo(Event.BuyProject, self.__revTrackerAcquired, lambda project: project == "RevTracker", True)
        Listener.listenTo(Event.BuyProject, self.__algoTradingAcquired,
                          lambda project: project == "Algorithmic Trading", True)
        Listener.listenTo(Event.BuyProject, self.__kill, lambda project: project == "Release the Hypnodrones", True)

        filter = lambda project: project in ("Hadwiger Clip Diagrams", "Improved MegaClippers",
                                             "Even Better MegaClippers", "Optimized MegaClippers")
        Listener.listenTo(Event.BuyProject, self.__clipperImprovementAcquired, filter, False)
        Listener.listenTo(Event.BuyProject, self.__megaClippersAcquired,
                          lambda project: project == "MegaClippers", True)
        Listener.listenTo(Event.BuyProject, self.__tokensBought,
                          lambda project: project == "Another Token of Goodwill", False)

        Listener.listenTo(Event.ButtonPressed, self.__moneyWithdrawn,
                          lambda button: button == "WithdrawFunds", False)

        # The exact project doesn't really matter, but this takes the pressure off the driver for the first part
        Listener.listenTo(Event.BuyProject, self.__killOfClipperAcquisition,
                          lambda project: project == "Hypnodrones", True)

    def __killOfClipperAcquisition(self, _: str):
        self.enoughClippers = True

    def __clipperImprovementAcquired(self, project: str) -> None:
        TS.print(f"Clipper improvement acquired: {project}.")
        if project == "Hadwiger Clip Diagrams":
            self.clipperSpeed += 5
        elif project == "Improved MegaClippers":
            self.megaPerformance += 0.25
        elif project == "Even Better MegaClippers":
            self.megaPerformance += 0.50
        elif project == "Optimized MegaClippers":
            self.megaPerformance += 1.00

        self.nextObjective = None

    def __megaClippersAcquired(self, _: str) -> None:
        self.noMegas = False
        self.nextObjective = None

    def __wireBuyerAcquired(self, _: str) -> None:
        self.killWire = True

    def __checkHedgeInits(self) -> None:
        # UGLY: but saves a bunch of additional code
        if self.hedgeInits == 0:
            self.runners.append(HedgeFunder(self.info, self.actions))

    def __revTrackerAcquired(self, _: str) -> None:
        thread = Process(target=self.pricer.activateRevTracker)
        thread.start()
        self.hedgeInits -= 1
        self.__checkHedgeInits()

    def __algoTradingAcquired(self, _: str) -> None:
        self.hedgeInits -= 1
        self.__checkHedgeInits()

    def __determineNextClipper(self):
        # Check which clipper to buy next
        if self.noMegas:
            return ("BuyAutoclipper", self.info.getFl("AutoCost"))

        # OPT: These prizes can probably be calculated as long as you track their count
        autoPrice, megaPrice = [self.info.getFl(clipCost) for clipCost in ("AutoCost", "MegaCost")]
        buyAuto = autoPrice / self.clipperSpeed < megaPrice / (self.megaPerformance * 500)
        nextClipper = "BuyAutoclipper" if buyAuto else "BuyMegaClipper"
        return (nextClipper, autoPrice) if buyAuto else (nextClipper, megaPrice)

    def __getMarketingCost(self) -> int:
        return 100 * (2 ** (self.marketingLevel - 1))

    def __giveNextObjective(self):
        clipper, clipperCost = self.__determineNextClipper()

        # TODO: Move this ratio to Config.
        if self.__getMarketingCost() < 2 * clipperCost:
            return ("LevelUpMarketing", self.__getMarketingCost())
        else:
            return (clipper, clipperCost)

    def __buyNextObjective(self):
        if not self.clippersAvailable:
            # You can't buy clippers untill you've made $5
            self.clippersAvailable = self.actions.isVisible("BuyAutoclipper")
            return

        if self.buyKilled or self.buyingOutGoodwill:
            return

        if self.enoughClippers and self.info.getInt("TotalClips") > 122_000_000:
            TS.print(f"Reached 122M clips in {TS.deltaStr(Config.get('Gamestart'))}, killing of Clipper acquisition.")
            self.buyKilled = True  # Kills of this method
            return

        # Occasionally buy some marketing instead
        # FIXME: Only save up for marketing if the cost can be achieved within the timeframe before investing starts
        if not self.nextObjective:
            self.nextObjective = self.__giveNextObjective()

        objectiveButton, objectiveCost = self.nextObjective
        funds = self.info.getFl("Funds")

        if objectiveButton == "LevelUpMarketing" and funds > self.highestWireCost + objectiveCost:
            self.actions.pressButton(objectiveButton)
            self.marketingLevel += 1
            self.nextObjective = None
        elif objectiveButton in ("BuyAutoclipper", "BuyMegaClipper") and funds > self.highestWireCost + objectiveCost:
            self.actions.pressButton(objectiveButton)
            self.nextObjective = None

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
        self.__buyNextObjective()
        for runner in self.runners:
            runner.tick()
