# Responsible for spending money on wire, clippers and marketing
from selenium.webdriver.common.by import By
from multiprocessing.dummy import Process
from Util.Files.Config import Config
from Util.GameLoop.Strategies.CurrentPhase import CurrentPhase, Phase
from Util.Listener import Event, Listener
from Util.Resources.HedgeFunder import HedgeFunder
from Util.Resources.PriceWatcher import PriceWatcher
from Webpage.PageState.PageActions import PageActions
from Webpage.PageState.PageInfo import PageInfo
from Util.Timestamp import Timestamp as TS
from Util.Flagbearer import FlagBearer
from enum import Enum, auto
from functools import partial


class Flag(Enum):
    WireProductionKilled = auto()
    ClippersForSale = auto()
    BuyingNextObjectiveKilled = auto()
    EnoughClippers = auto()
    BuyingOutGoodwill = auto()
    MegaClippersAvailable = auto()


class CashSpender():

    def __moneyWithdrawn(self, _: str) -> None:
        """Checks if enough money is withdrawn to buy out all Tokens of Goodwill. This will temporarily block all clipper acquisitions."""
        self.flags[Flag.BuyingOutGoodwill] = self.tokensOfGoodwill > 0 and (self.info.getFl("Funds") > 511_500_000.0)

    def __tokensBought(self, _: str) -> None:
        """Keeps track of the amount of Tokens of Goodwill being acquired. Once they're all bought, clipper acquisition can resume."""
        self.tokensOfGoodwill -= 1
        if self.tokensOfGoodwill <= 0:
            self.flags[Flag.BuyingOutGoodwill] = False

    def __init__(self, pageInfo: PageInfo, pageActions: PageActions) -> None:
        self.info = pageInfo
        self.actions = pageActions

        self.highestWireCost = 27
        self.clipperSpeed = 2.5
        self.megaPerformance = 1
        self.nextObjective = None
        self.pricer = PriceWatcher(self.info, self.actions)
        self.runners = [self.pricer]
        self.hedgeInits = 2

        self.flags = FlagBearer(
            true=(),
            false=(Flag.WireProductionKilled, Flag.ClippersForSale, Flag.BuyingNextObjectiveKilled,
                   Flag.EnoughClippers, Flag.BuyingOutGoodwill, Flag.MegaClippersAvailable))
        self.marketingCost = lambda: 100 * (2 ** (self.marketingLevel - 1))

        self.marketingLevel = 1
        self.tokensOfGoodwill = Config.get("phaseOneProjects").count("Another Token of Goodwill")

        # UGLY: this class probably needs some splitting up
        Listener.listenTo(Event.BuyProject, self.__revTrackerAcquired, "RevTracker", True)
        Listener.listenTo(Event.BuyProject, self.__algoTradingAcquired, "Algorithmic Trading", True)
        filter = lambda project: project in ("Hadwiger Clip Diagrams", "Improved MegaClippers",
                                             "Even Better MegaClippers", "Optimized MegaClippers")
        Listener.listenTo(Event.BuyProject, self.__clipperImprovementAcquired, filter, False)
        Listener.listenTo(Event.BuyProject, self.__megaClippersAcquired, "MegaClippers", True)
        Listener.listenTo(Event.BuyProject, self.__tokensBought, "Another Token of Goodwill", False)
        Listener.listenTo(Event.ButtonPressed, self.__moneyWithdrawn, "WithdrawFunds", False)
        Listener.listenTo(Event.BuyProject, partial(self.flags.set, Flag.WireProductionKilled, True), "WireBuyer", True)

        # The exact project doesn't really matter, but this takes the pressure off the driver for the first part
        Listener.listenTo(Event.BuyProject, self.__killOfClipperAcquisition, "Hypnodrones", True)

    def __killOfClipperAcquisition(self, _: str):
        self.flags[Flag.EnoughClippers] = True

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
        TS.print("Enabled Megaclippers for sale")
        self.flags[Flag.MegaClippersAvailable] = True
        self.nextObjective = None

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
        if not self.flags[Flag.MegaClippersAvailable]:
            return ("BuyAutoclipper", self.info.getFl("AutoCost"))

        # OPT: These prizes can probably be calculated as long as you track their count
        autoPrice, megaPrice = [self.info.getFl(clipCost) for clipCost in ("AutoCost", "MegaCost")]
        buyAuto = autoPrice / self.clipperSpeed < megaPrice / (self.megaPerformance * 500)
        nextClipper = "BuyAutoclipper" if buyAuto else "BuyMegaClipper"
        return (nextClipper, autoPrice) if buyAuto else (nextClipper, megaPrice)

    def __giveNextObjective(self):
        clipper, clipperCost = self.__determineNextClipper()

        # TODO: Move this ratio to Config.
        if self.marketingCost() < 2 * clipperCost:
            return ("LevelUpMarketing", self.marketingCost())
        else:
            return (clipper, clipperCost)

    def __buyNextObjective(self):
        if not self.flags[Flag.ClippersForSale]:
            # You can't buy clippers untill you've made $5
            self.flags[Flag.ClippersForSale] = self.actions.isVisible("BuyAutoclipper")
            return

        if self.flags[Flag.BuyingNextObjectiveKilled] or self.flags[Flag.BuyingOutGoodwill]:
            return

        if self.flags[Flag.EnoughClippers] and self.info.getInt("TotalClips") > 122_000_000:
            TS.print(f"Reached 122M clips in {TS.deltaStr(Config.get('Gamestart'))}, killing of Clipper acquisition.")
            self.flags[Flag.BuyingNextObjectiveKilled] = True  # Kills of this method
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
        if self.flags[Flag.WireProductionKilled]:
            return

        wireCost = self.info.getInt("WireCost")
        self.highestWireCost = max(wireCost, self.highestWireCost)

        if self.info.getFl("Funds") < wireCost:
            return

        wire = self.info.getInt("Wire")
        if wire < 500 or (
                wire < 1500 and wireCost / self.highestWireCost <= 0.65) or (
                wire < 2500 and wireCost / self.highestWireCost <= 0.50):  # Either buy when low or cheap
            self.actions.pressButton("BuyWireSpool")

    def tick(self):
        self.__updateWire()
        self.__buyNextObjective()

        for runner in self.runners:
            runner.tick()
