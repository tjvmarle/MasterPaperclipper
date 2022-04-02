# Responsible for managing Investments

import time
from Util.Files.Config import Config
from Webpage.PageState.PageActions import PageActions
from Webpage.PageState.PageInfo import PageInfo
from Util.Timestamp import Timestamp as TS
from Util.Listener import Event, Listener


class HedgeFunder():
    def __yomiEnabled(self, _: str) -> None:
        self.yomiAvailable = True

    def __limitBreak(self, _: str) -> None:
        TS.print(f"Limit break enabled. Stonks only go up!")
        self.myFinalForm = True

    def __fullMonoAcquired(self, _: str) -> None:
        self.fullMonoAcq = True

    def __init__(self, pageInfo: PageInfo, pageActions: PageActions) -> None:
        self.info = pageInfo
        self.actions = pageActions

        self.investmentsActive = False
        self.myFinalForm = False
        self.currLevel = 0
        self.highRisk = False
        self.noMoreInvesting = False
        self.fullMonoAcq = False
        self.yomiAvailable = False
        # TODO: Move these buffers to Config
        self.takeOuts = [("Hostile Takeover", 1_500_000), ("Full Monopoly", 11_000_000)]
        self.investTime = float(Config.get("InvestPercentage")) * 0.6
        self.currMinute = TS.now().minute
        self.InvestUpgradeCosts = [int(cost) for cost in Config.get("InvestUpgradeCosts")]

        Listener.listenTo(Event.BuyProject, self.__fullMonoAcquired, lambda project: project == "Full Monopoly", True)
        Listener.listenTo(Event.BuyProject, self.__limitBreak, lambda project: project == "Theory of Mind", True)
        Listener.listenTo(Event.BuyProject, self.__yomiEnabled, lambda project: project == "Strategic Modeling", True)

    def invest(self):
        # TODO: stop investing when all tokens off goodwill have been bought. Drain remaining cash for buying clippers.
        # OPT: Perhaps use the TS.timer for this
        now = TS.now()
        if self.currMinute == now.minute and not self.investmentsActive:
            return
        elif not self.investmentsActive:
            self.investmentsActive = True  # Start investments
            self.investStart = now
            self.currMinute = now.minute

        if TS.delta(self.investStart) > self.investTime:
            self.investmentsActive = False  # Stop investments

        # Wire is cheap and this prevents production blockage
        # if self.info.getInt("Wire") < 20_000:
        #     # FIXME: This one also cause quite some errors
            self.actions.pressButton("BuyWire")

        self.actions.pressButton("DepositFunds")

    def setRiskLevel(self):
        if not self.highRisk and self.currLevel > 2:
            # Options: Low Risk, Med Risk, High Risk
            self.actions.selectFromDropdown("InvestRisk", "High Risk")
            self.highRisk = True

    def setInvestmentLevel(self):
        if (self.currLevel >= 10 and not self.myFinalForm) or not self.InvestUpgradeCosts or not self.yomiAvailable:
            return

        currYomi = self.info.getInt("Yomi")
        if self.currLevel >= 6 and not self.fullMonoAcq:
            # Ensure a 3k buffer to always allow Full Monopoly to be bought
            currYomi -= 3_000

        # OPT: Don't by too many of these, as Yomi is very important in Phase3
        if currYomi > self.InvestUpgradeCosts[0] and self.actions.pressButton("UpgradeInvestLevel"):
            self.currLevel += 1
            self.InvestUpgradeCosts.pop(0)

    def takeOut(self):
        if not self.takeOuts:
            return

        availableCash = self.info.getFl("LiquidAssets")
        project, minCashAvailable = self.takeOuts[0]

        if availableCash > minCashAvailable and self.actions.isVisible(project):
            TS.print(f"Withdrawing ${availableCash} to buy {project}.")
            self.actions.pressButton("WithdrawFunds")
            time.sleep(0.5)
            result = self.actions.pressButton(project)
            if not self.actions.isVisible(project):
                # FIXME: Apparently this still fails sometimes. Add a check if the project if really gone.
                TS.print(f"Buying {project} was successful.")
            else:
                TS.print(f"Buying {project} failed.")
            self.actions.pressButton("BuyWire")
            self.actions.pressButton("DepositFunds")
            self.takeOuts.pop(0)

    def aTokenOfGoodwill(self) -> None:
        if self.takeOuts or self.noMoreInvesting:  # or self.info.getInt("Trust") > 90:
            return

        availableCash = self.info.getFl("LiquidAssets")

        # OPT: Enable buying additional trust if investments for some reason go beyond 1 billion.
        if availableCash < 511_500_000.0:  # This covers 10 acquisitions
            return

        self.actions.pressButton("WithdrawFunds")
        cash = self.info.getFl("Funds")
        if cash < 511_500_000.0:
            # Race condition.
            TS.print(f"Money withdrawal failed.")
            self.actions.pressButton("BuyWire")
            self.actions.pressButton("DepositFunds")
            return

        self.noMoreInvesting = True
        return

    def __emptyAccount(self) -> None:
        if self.info.getFl("LiquidAssets") > 0:
            self.actions.pressButton("WithdrawFunds")

    def tick(self):
        if self.noMoreInvesting:
            self.__emptyAccount()
        else:
            self.setRiskLevel()
            self.setInvestmentLevel()
            self.invest()
            self.takeOut()
            self.aTokenOfGoodwill()
