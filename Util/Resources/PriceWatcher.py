from Webpage.PageState.PageActions import PageActions
from Webpage.PageState.PageInfo import PageInfo
from Util.Timestamp import Timestamp as TS


class PriceWatcher():
    def __init__(self, pageInfo: PageInfo, pageActions: PageActions) -> None:
        self.info = pageInfo
        self.actions = pageActions
        self.priceAdjustmentTime = 3.0
        self.lastPriceAdjustment = TS.now()
        self.demand = self.info.getInt("Demand")

    def __adjustPrice(self):
        rate, unsold = [self.info.getInt(field) for field in ("ClipsPerSec", "Unsold")]

        demand = self.info.getInt("Demand")
        while rate > 0 and demand > 5 * rate:  # Emergency handling for large changes in marketing
            self.actions.pressButton("RaisePrice")
            self.info.update("Demand")
            demand = self.info.getInt("Demand")

        lastAdjustment = TS.delta(self.lastPriceAdjustment)

        if lastAdjustment > 0.25 and unsold < rate:  # Emergency handling for low stock in marketing
            self.actions.pressButton("RaisePrice")
            return

        if lastAdjustment > 0.25 and unsold > 20 * rate:  # Emergency handling for low stock in marketing
            self.actions.pressButton("LowerPrice")
            return

        if lastAdjustment < self.priceAdjustmentTime:
            return

        # OPT: Maybe couple Market Demand with production speed instead
        if unsold > 10 * rate:
            self.actions.pressButton("LowerPrice")
            if self.actions.isEnabled("LowerPrice"):
                self.actions.pressButton("LowerPrice")
            self.priceAdjustmentTime += 0.5
        elif unsold > 6 * rate:
            self.actions.pressButton("LowerPrice")
            self.priceAdjustmentTime += 0.5
        elif unsold < 3 * rate:
            self.actions.pressButton("RaisePrice")
            self.priceAdjustmentTime += 0.5
        else:
            self.priceAdjustmentTime = 3.0

        self.lastPriceAdjustment = TS.now()

    def tick(self):
        self.__adjustPrice()
