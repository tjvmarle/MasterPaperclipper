# Responsible for spending money on wire, clippers and marketing
from Webpage.PageState.PageActions import PageActions
from Webpage.PageState.PageInfo import PageInfo


class CashSpender():
    def __init__(self, pageInfo: PageInfo, pageActions: PageActions) -> None:
        self.info = pageInfo
        self.actions = pageActions
        self.highestWireCost = 27

    def saveUp(self, buffer: int) -> None:
        # Sets a new lower limit for fundsd to reach after buying clippers etc.
        pass

    def __buyClippers(self):
        autoCost = self.info.getFl("AutoCost")
        if not autoCost:
            return

        enoughMoney = (self.info.getFl("Funds") - self.highestWireCost) > autoCost
        if enoughMoney and self.info.getInt("AutoCount") < 75:
            self.actions.pressButton("BuyAutoclipper")
            self.info.update("Funds")

    def __updateWire(self):
        wireCost = self.info.getInt("WireCost")
        self.highestWireCost = max(wireCost, self.highestWireCost)

        if self.info.getFl("Funds") < wireCost:
            return

        wire = self.info.getInt("Wire")
        if wire < 200 or (
                wire < 1500 and wireCost / self.highestWireCost <= 0.6) or (
                wire < 2500 and wireCost / self.highestWireCost <= 0.45):  # Either buy when low or cheap
            self.actions.pressButton("BuyWire")

    def tick(self):
        self.__updateWire()
        self.__buyClippers()
