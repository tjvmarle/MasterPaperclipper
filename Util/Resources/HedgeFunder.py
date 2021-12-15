# Responsible for managing Investments

import time
from Util.Files.Config import Config
from Webpage.PageState.PageActions import PageActions
from Webpage.PageState.PageInfo import PageInfo
from Util.Timestamp import Timestamp as TS

# TODO: Phase 1 ends at 100 trust. We need to buy around 10-20 trust from projects.
# We first need 1 million to buy our competitor.
# After that we need 10 million to buy out all competition.
# Buying 10 trust after that requires 512 million.


class HedgeFunder():
    def __init__(self, pageInfo: PageInfo, pageActions: PageActions) -> None:
        self.info = pageInfo
        self.actions = pageActions

        self.investmentsActive = False
        self.currLevel = 0
        self.highRisk = False
        self.takeOuts = [("Hostile Takeover", 1_500_000), ("Full Monopoly", 11_000_000)]
        self.investTime = float(Config.get("InvestPercentage")) * 0.6
        self.currMinute = TS.now().minute

    def invest(self):
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
        if self.currLevel >= 8:
            # You only need about 86.000 yomi for phase 2 in total
            # TODO: Even more levels could be bought is Theory of Mind is acquired
            return

        if self.actions.isEnabled("UpgradeInvestLevel") and self.actions.pressButton("UpgradeInvestLevel"):
            self.currLevel += 1

    def takeOut(self):
        if not self.takeOuts:
            return

        availableCash = self.info.getFl("LiquidAssets")
        project, minCashAvailable = self.takeOuts[0]

        if availableCash > minCashAvailable and self.actions.isVisible(project):
            self.actions.pressButton("WithdrawFunds")
            time.sleep(0.5)
            self.actions.pressButton(project)
            self.actions.pressButton("DepositFunds")
            self.takeOuts.pop(0)

    def aTokenOfGoodwill(self) -> None:
        if self.takeOuts:
            return

        availableCash = self.info.getFl("LiquidAssets")

        # OPT: Reaching 90 trust requires 121.4M clips. You also want to reach both points as close to eachother as possible.
        if availableCash < 511_500_000.0:  # This covers 10 acquisitions
            if self.info.getInt("Wire") < 20_000:
                self.actions.pressButton("BuyWire")
            self.actions.pressButton("DepositFunds")
            # FIXME: this triggers 100% of the time once self.takeOuts is empty. This should maybe only happen once trust reaches 90
            return

        self.actions.pressButton("WithdrawFunds")
        self.actions.pressButton("A Token of Goodwill")
        for _ in range(0, 9):
            time.sleep(0.5)
            self.actions.pressButton("Another Token of Goodwill")

        # Trustspender runs after this one in the same loop, so trust should've been spent before the Hypnodrones are released.

    def tick(self):
        self.setRiskLevel()
        self.setInvestmentLevel()
        self.invest()
        self.takeOut()
        self.aTokenOfGoodwill()
