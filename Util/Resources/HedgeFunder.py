# Responsible for Investments

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

        self.actions.pressButton("DepositFunds")

        if TS.delta(self.investStartTime) > self.investTime:
            self.investmentsActive = False

    def checkIncome(self):
        if not self.investLevels:
            return

        if self.info.getFl("RevPerSec") > self.investLevels[0]:
            self.investmentsActive = True
            self.investStartTime = TS.now()
            self.investLevels.pop(0)

    def setRisk(self):
        if not self.highRisk and self.currLevel > 2:
            # Options: Low Risk, Med Risk, High Risk
            self.actions.selectFromDropdown("InvestRisk", "High Risk")
            self.highRisk = True

    def setLevel(self):
        if self.currLevel >= 5:
            return

        # Yomi costs for Invest Upgrades: 100 (54), 658 (55), 1981 (56), 4330 (57), 7943 (58), 13038 (59)
        if self.actions.isEnabled("UpgradeInvestLevel") and self.actions.pressButton("UpgradeInvestLevel"):
            self.currLevel += 1

    def tick(self):
        self.setRisk()
        self.setLevel()
        self.checkIncome()
        self.invest()

# TODO: Phase 1 ends at 100 trust. We need to buy around 10-20 trust from projects.
# We first need 1 million to buy our competitor.
# After that we need 10 million to buy out all competition.
# Buying 10 trust after that requires 512 million.
# Perhaps don't even buy the project until you're ready to invest immediately
# Find a way to block other funds spending until you're done investing
