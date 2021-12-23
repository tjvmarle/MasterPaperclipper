# Responsible for managing Investments

import time
from Util.Files.Config import Config
from Webpage.PageState.PageActions import PageActions
from Webpage.PageState.PageInfo import PageInfo
from Util.Timestamp import Timestamp as TS
from Util.Listener import Event, Listener


class HedgeFunder():
    def limitBreak(self) -> None:
        TS.print(f"Limit break enabled. Stonks only go up!")
        self.myFinalForm = True

    def __init__(self, pageInfo: PageInfo, pageActions: PageActions) -> None:
        self.info = pageInfo
        self.actions = pageActions

        self.investmentsActive = False
        self.myFinalForm = False
        self.currLevel = 0
        self.highRisk = False
        self.noMoreGoodwill = False
        self.takeOuts = [("Hostile Takeover", 1_500_000), ("Full Monopoly", 11_000_000)]
        self.investTime = float(Config.get("InvestPercentage")) * 0.6
        self.currMinute = TS.now().minute

        Listener.listenTo(Event.BuyProject, self.limitBreak, lambda project: project == "Theory of Mind", True)

    def invest(self):
        # TODO: stop investing when all tokens off goodwill have been bought. Keep remaining cash for buying clippers.
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
        if self.info.getInt("Wire") < 20_000:
            self.actions.pressButton("BuyWire")

        self.actions.pressButton("DepositFunds")

    def setRiskLevel(self):
        if not self.highRisk and self.currLevel > 2:
            # Options: Low Risk, Med Risk, High Risk
            self.actions.selectFromDropdown("InvestRisk", "High Risk")
            self.highRisk = True

    def setInvestmentLevel(self):
        if self.currLevel >= 10 and not self.myFinalForm:
            # You only need about 86.000 yomi for phase 2 in total
            # TODO: Even more levels could be bought is Theory of Mind is acquired
            return

        if self.currLevel >= 8:
            # Ensure a 3k buffer to always allow Full Monopoly to be bought
            yomiCost = self.info.getInt("InvestUpgradeCost")
            yomiStash = self.info.getInt("Yomi")
            if yomiStash < (yomiCost + 3_000):
                return

        if self.actions.isEnabled("UpgradeInvestLevel") and self.actions.pressButton("UpgradeInvestLevel"):
            self.currLevel += 1

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
            if result:
                # FIXME: Apparently this still fails sometimes. Add a check if the project if really gone.
                TS.print(f"Buying {project} was successful.")
            else:
                TS.print(f"Buying {project} failed.")
            self.actions.pressButton("DepositFunds")
            self.takeOuts.pop(0)

    def aTokenOfGoodwill(self) -> None:
        if self.takeOuts or self.noMoreGoodwill or self.info.getInt("Trust") > 90:
            return

        availableCash = self.info.getFl("LiquidAssets")

        # OPT: Enable buying additional trust if investments for some reason go beyond 1 billion.
        if availableCash < 511_500_000.0:  # This covers 10 acquisitions
            return

        self.actions.pressButton("WithdrawFunds")
        cash = self.info.getFl("Funds")
        TS.print(f"Funds withdrawn, available cash is: {cash}.")
        if cash < 511_500_000.0:
            # Something went wrong.
            TS.print(f"Money withdrawal failed.")
            self.actions.pressButton("DepositFunds")
            return

        self.actions.pressButton("A Token of Goodwill")
        for _ in range(0, 9):
            time.sleep(0.5)
            self.actions.pressButton("Another Token of Goodwill")
        self.noMoreGoodwill = True
        time.sleep(0.5)

    def tick(self):
        self.setRiskLevel()
        self.setInvestmentLevel()
        self.invest()
        self.takeOut()
        self.aTokenOfGoodwill()
