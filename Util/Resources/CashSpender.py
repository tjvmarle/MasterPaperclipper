# Responsible for spending money on wire, clippers and marketing
from Webpage.PageState.PageActions import PageActions
from Webpage.PageState.PageInfo import PageInfo
from Util.Timestamp import Timestamp as TS


class CashSpender():
    def __init__(self, pageInfo: PageInfo, pageActions: PageActions) -> None:
        self.info = pageInfo
        self.actions = pageActions
        self.highestWireCost = 27
        self.clipperSpeed = 2.5  # Includes most of the upgrades
        self.megaPerformance = 1
        self.megaSpeed = lambda: self.megaPerformance * 500
        self.nextClipper = "BuyAutoclipper"
        self.killWire = False

    def projectAcquired(self, project: str):
        if project == "WireBuyer":
            TS.print(f"Killed the WireWatcher.")
            self.killWire = True
        elif project == "Hadwiger Clip Diagrams":
            self.clipperSpeed += 5
        elif project == "Improved MegaClippers":
            self.megaPerformance += 0.25
        elif project == "Even Better MegaClippers":
            self.megaPerformance += 0.50
        elif project == "Optimized MegaClippers":
            self.megaPerformance += 1.00

    def getCallback(self):
        return self.projectAcquired

    def __determineClipper(self) -> float:
        # Check which clipper to buy next
        if not self.actions.isVisible("BuyMegaClipper"):
            return self.info.getFl("AutoCost")

        autoPrice, megaPrice = [self.info.getFl(clipCost) for clipCost in ("AutoCost", "MegaCost")]
        buyAuto = autoPrice / self.clipperSpeed < megaPrice / self.megaSpeed()
        self.nextClipper = "BuyAutoclipper" if buyAuto else "BuyMegaClipper"
        return autoPrice if buyAuto else megaPrice

    def __buy(self):
        if not self.actions.isVisible("BuyAutoclipper"):  # You can't buy clippers untill you've made $5
            return

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
