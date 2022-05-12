# Responsible for managing Investments

import time
from Util.Files.Config import Config
from Webpage.PageState.PageActions import PageActions
from Webpage.PageState.PageInfo import PageInfo
from Util.Timestamp import Timestamp as TS
from Util.Listener import Event, Listener


class HedgeFunder():
    """Manages the investment engine. Occasionally takes out money to buy projects."""

    def __depositFunds(self) -> None:
        """Deposit funds in the investment machine, but try to ensure you don't run completely dry on wire."""
        if not self.actions.isEnabled("BuyWireSpool"):
            return

        if TS.delta(self.lastWireMoment) > 1.5 and not self.info.getInt("Wire") < 10_000:
            self.actions.pressButton("BuyWireSpool")
            self.lastWireMoment = TS.now()

        self.actions.pressButton("DepositFunds")

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

        # TODO: Change to internal state
        self.investmentsActive = False
        self.myFinalForm = False
        self.currLevel = 0
        self.highRisk = False
        self.noMoreInvesting = False
        self.fullMonoAcq = False
        self.yomiAvailable = False
        self.lastWireMoment = TS.now()

        # TODO: Move these buffers to Config
        self.cashProjects = [("Hostile Takeover", 1_100_000), ("Full Monopoly", 11_000_000)]
        self.investTime = float(Config.get("InvestPercentage")) * 0.6
        self.currMinute = TS.now().minute
        self.InvestUpgradeCosts = [int(cost) for cost in Config.get("InvestUpgradeCosts")]

        Listener.listenTo(Event.BuyProject, self.__fullMonoAcquired, "Full Monopoly", True)
        Listener.listenTo(Event.BuyProject, self.__limitBreak, "Theory of Mind", True)
        Listener.listenTo(Event.BuyProject, self.__yomiEnabled, "Strategic Modeling", True)

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

        self.__depositFunds()

    def setRiskLevel(self):
        if not self.highRisk and self.currLevel > 2:
            # Options: Low Risk, Med Risk, High Risk
            self.actions.selectFromDropdown("InvestRisk", "High Risk")
            self.highRisk = True

    def setInvestmentLevel(self):
        if self.currLevel >= int(Config.get("MaxInvestLevel")):
            return

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
        """Manages acquisition of two specific projects requiring cash. This doesn't mix well otherwise with the clipper acquisitions or ProjectBuyer."""
        if not self.cashProjects:
            return

        availableCash = self.info.getFl("LiquidAssets")
        project, minCashRequirement = self.cashProjects[0]

        if availableCash > minCashRequirement and self.actions.isVisible(project):

            TS.print(f"Withdrawing ${availableCash} to buy {project}.")
            self.actions.pressButton("WithdrawFunds")

            time.sleep(0.25)
            self.actions.pressButton(project)
            time.sleep(0.25)

            # Some safety to check if acquisition was actually successful.
            if not self.actions.isVisible(project):
                TS.print(f"Buying {project} was successful.")
                self.cashProjects.pop(0)
            else:
                TS.print(f"Buying {project} failed.")
                self.__depositFunds()

    def aTokenOfGoodwill(self) -> None:
        if self.cashProjects or self.noMoreInvesting:
            return

        # Tokens of goodwill become available at 100M clips.
        if self.info.getFl("LiquidAssets") < 511_500_000.0:  # This covers 10 acquisitions
            return

        self.actions.pressButton("WithdrawFunds")
        cash = self.info.getFl("Funds")
        if cash < 511_500_000.0:
            # Race condition.
            TS.print(f"Money withdrawal failed.")
            self.__depositFunds()
            return

        self.noMoreInvesting = True

    def __emptyAccount(self) -> None:
        if self.info.getFl("LiquidAssets") > 0:
            self.actions.pressButton("WithdrawFunds")

    def tick(self) -> None:
        if self.noMoreInvesting:
            self.__emptyAccount()
        else:
            self.setRiskLevel()
            self.setInvestmentLevel()
            self.invest()
            self.takeOut()
            self.aTokenOfGoodwill()
