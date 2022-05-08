# Responsible for spending money on wire, clippers and marketing
from Util.Files.Config import Config
from Util.Listener import Event, Listener
from Util.Resources.OrderedEnum import OrderedEnum
from Util.Resources.PhaseOne.HedgeFunder import HedgeFunder
from Util.Resources.PhaseOne.PriceWatcher import PriceWatcher
from Util.Resources.StatefulRunner import StatefulRunner
from Webpage.PageState.PageActions import PageActions
from Webpage.PageState.PageInfo import PageInfo
from Util.Timestamp import Timestamp as TS
from Util.Flagbearer import FlagBearer
from enum import Enum, auto
from functools import partial


class Flag(Enum):
    # TODO: Change these to states
    BuyingOutGoodwill = auto()


class CashSpender(StatefulRunner):
    """Manages the spending of our disposable income."""

    class States(OrderedEnum):
        NoClippersAvailable = 0    # Game start, can't buy clippers yet
        ClippersAvailable = 1      # Autoclippers for sale
        WireBuyerAcquired = 4      # Wirebuyer acquired, no additional actions required anymore
        MegaClippersAvailable = 5  # Start taking megaclippers into consideration when determining next item to buy

    def __moneyWithdrawn(self, _: str) -> None:
        """Checks if enough money is withdrawn to buy out all Tokens of Goodwill. This will temporarily block all 
        clipper acquisitions. Regular games should buy 10 tokens. Slower ones will buy 9, since an additional trust is 
        gained through clip production."""

        total_cost: int = 0
        for power in range(100 - self.info.getInt("Trust")):
            total_cost += 500_000 * 2 ** power

        self.flags[Flag.BuyingOutGoodwill] = self.tokensOfGoodwill > 0 and (
            self.info.getFl("Funds") > float(total_cost))

    def __tokensBought(self, _: str) -> None:
        """Keeps track of the amount of Tokens of Goodwill being acquired. Once they're all bought, clipper acquisition 
        can resume."""

        self.tokensOfGoodwill -= 1
        if self.tokensOfGoodwill <= 0:
            self.flags[Flag.BuyingOutGoodwill] = False

    def __init__(self, pageInfo: PageInfo, pageActions: PageActions) -> None:
        super().__init__(pageInfo, pageActions, CashSpender.States)
        self.states: CashSpender.States

        self.highestWireCost = 27
        self.clipperSpeed = 2.5
        self.megaPerformance = 1
        self.nextObjective = None

        self.delegates = [pricer := PriceWatcher(self.info, self.actions)]
        self.runners = [self.__updateWire, self.__buyNextObjective, pricer.tick]

        self.flags = FlagBearer(true=(), false=(Flag.BuyingOutGoodwill, ))
        self.marketingCost = lambda: 100 * (2 ** (self.marketingLevel - 1))

        self.marketingLevel = 1
        self.tokensOfGoodwill = Config.get("phaseOneProjects").count("Another Token of Goodwill")

        # UGLY: this class probably needs some splitting up
        Listener.listenTo(Event.BuyProject, self.__algoTradingAcquired, "Algorithmic Trading", True)
        def filter(project): return project in ("Hadwiger Clip Diagrams", "Improved MegaClippers",
                                                "Even Better MegaClippers", "Optimized MegaClippers")
        Listener.listenTo(Event.BuyProject, self.__clipperImprovementAcquired, filter, False)
        Listener.listenTo(Event.BuyProject, self.__megaClippersAcquired, "MegaClippers", True)
        Listener.listenTo(Event.BuyProject, self.__tokensBought, "Another Token of Goodwill", False)
        Listener.listenTo(Event.ButtonPressed, self.__moneyWithdrawn, "WithdrawFunds", False)

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
        self.currentState.goTo(self.states.MegaClippersAvailable)
        self.nextObjective = None

    def __algoTradingAcquired(self, _: str) -> None:
        self.delegates.append(hedger := HedgeFunder(self.info, self.actions))
        self.runners.append(hedger.tick)

    def __determineNextClipper(self):
        """Checks which clipper to buy next. Basically calculates production speed per dollar spent and returns the most
        optimal item."""
        if self.currentState.before(self.states.MegaClippersAvailable):
            return ("BuyAutoclipper", self.info.getFl("AutoCost"))

        # OPT: These prizes can probably be calculated as long as you track their count
        autoPrice, megaPrice = [self.info.getFl(clipCost) for clipCost in ("AutoCost", "MegaCost")]
        buyAuto = autoPrice / self.clipperSpeed < megaPrice / (self.megaPerformance * 500)
        nextClipper = "BuyAutoclipper" if buyAuto else "BuyMegaClipper"
        return (nextClipper, autoPrice) if buyAuto else (nextClipper, megaPrice)

    def __giveNextObjective(self):
        """Determines next objective to buy, either a specific autoclipper or upgrading Marketing level."""
        clipper, clipperCost = self.__determineNextClipper()

        if self.marketingCost() < int(Config.get('MarketingRatio')) * clipperCost:

            # Only save up for marketing if the cost can be achieved within the timeframe before investing starts.
            availSavingTime = 60 - Config.getInt('InvestPercentage') * 0.6
            maxCash = 0
            try:
                maxCash = availSavingTime * self.info.getFl("RevPerSec")
            except:
                pass

            if maxCash > self.marketingCost():
                return ("LevelUpMarketing", self.marketingCost())

        return (clipper, clipperCost)

    def __buyNextObjective(self):
        """Buys the next objective if possible. Keeps a buffer to always allow buying wire."""

        if self.currentState.before(self.states.ClippersAvailable):
            if self.actions.isVisible("BuyAutoclipper"):
                self.currentState.goTo(self.states.ClippersAvailable)
            else:
                return

        if self.flags[Flag.BuyingOutGoodwill]:
            return

        if self.info.getInt("TotalClips") > 122_000_000:
            TS.print(f"Reached 122M clips in {TS.deltaStr(Config.get('Gamestart'))}, killing of Clipper acquisition.")
            self.runners.remove(self.__buyNextObjective)  # Kills of this method
            return

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
        """Buys wire if possible and required. Tries to buy cheap."""

        if self.currentState.atLeast(self.states.WireBuyerAcquired):
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
