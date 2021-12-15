# Responsible for Investments

import time
from Util.Files.Config import Config
from Webpage.PageState.PageActions import PageActions
from Webpage.PageState.PageInfo import PageInfo
from Util.Timestamp import Timestamp as TS


class HedgeFunder():
    def __init__(self, pageInfo: PageInfo, pageActions: PageActions) -> None:
        self.info = pageInfo
        self.actions = pageActions

        self.investmentsActive = False
        self.investLevels = [float(income) for income in Config.get("InvestLevels")]
        self.investTime = float(Config.get("InvestPeriod"))
        self.currLevel = 0
        self.highRisk = False

    def invest(self):
        if not self.investmentsActive:
            return

        self.actions.pressButton("BuyWire")  # Wire is cheap and this prevents production blockage
        self.actions.pressButton("DepositFunds")

        if TS.delta(self.investStartTime) > self.investTime:
            self.investmentsActive = False
            TS.print(f"Stop investing.")

    def checkIncome(self):
        if not self.investLevels:
            return

        if not self.investmentsActive and self.info.getFl("RevPerSec") > self.investLevels[0]:
            # TODO: Trigger investments as percentage of time
            TS.print(f"Start investing at {self.investLevels[0]}.")
            self.investmentsActive = True
            self.investStartTime = TS.now()
            self.investLevels.pop(0)

    def setRisk(self):
        if not self.highRisk and self.currLevel > 2:
            # Options: Low Risk, Med Risk, High Risk
            self.actions.selectFromDropdown("InvestRisk", "High Risk")
            self.highRisk = True

    def setLevel(self):
        if self.currLevel >= 6:
            return

        if self.actions.isEnabled("UpgradeInvestLevel") and self.actions.pressButton("UpgradeInvestLevel"):
            self.currLevel += 1

    def takeOut(self):
        # Don't drain all savings at once
        # FIXME: This crashes the script when encountering the cash value a 2nd time.
        if self.info.getFl("LiquidAssets") > 2_000_000 and self.actions.isVisible("Hostile Takeover"):
            TS.print("Withdraw for Hostile Takeover!")
            self.actions.pressButton("WithdrawFunds")
            time.sleep(0.5)
            self.actions.pressButton("Hostile Takeover")
            self.actions.pressButton("DepositFunds")

    def tick(self):
        self.setRisk()
        self.setLevel()
        self.checkIncome()
        self.invest()
        self.takeOut()

# TODO: Phase 1 ends at 100 trust. We need to buy around 10-20 trust from projects.
# We first need 1 million to buy our competitor.
# After that we need 10 million to buy out all competition.
# Buying 10 trust after that requires 512 million.
# Perhaps don't even buy the project until you're ready to invest immediately
# Find a way to block other funds spending until you're done investing
