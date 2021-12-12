from Webpage.PageState.PageActions import PageActions
from Webpage.PageState.PageInfo import PageInfo
from Util.Timestamp import Timestamp as TS


class PriceWatcher():
    def __init__(self, pageInfo: PageInfo, pageActions: PageActions) -> None:
        self.info = pageInfo
        self.actions = pageActions
        self.priceAdjustmentTime = 5.0
        self.lastPriceAdjustment = TS.now()
        self.demand = self.info.getInt("Demand")

    def __adjustPrice(self):
        rate, unsold = [self.info.getInt(field) for field in ("ClipsPerSec", "Unsold")]

        # TODO: Add emergency adjustment for too much stock!

        demand = self.info.getInt("Demand")
        while rate > 0 and demand > 5 * rate:  # Emergency handling for large changes in marketing
            TS.print(f"Emergency price raise, demand too high! Rate: {rate}, demand {demand}.")
            self.actions.pressButton("RaisePrice")
            self.info.update("Demand")
            demand = self.info.getInt("Demand")

        lastAdjustment = TS.delta(self.lastPriceAdjustment)

        if lastAdjustment > 0.25 and unsold < rate:  # Emergency handling for low stock in marketing
            TS.print(f"Emergency price raise! Unsold: {unsold}, rate: {rate}.")
            self.actions.pressButton("RaisePrice")
            return

        if lastAdjustment > 0.25 and unsold > 20 * rate:  # Emergency handling for low stock in marketing
            TS.print(f"Emergency price drop! Unsold: {unsold}, rate: {rate}.")
            self.actions.pressButton("LowerPrice")
            return

        if lastAdjustment < self.priceAdjustmentTime:
            return

        # OPT: Maybe couple Market Demand with production speed instead
        if unsold > 10 * rate:
            TS.print(f"Double price drop.")
            self.actions.pressButton("LowerPrice")
            self.actions.pressButton("LowerPrice")
            self.priceAdjustmentTime += 0.5
        elif unsold > 6 * rate:
            TS.print(f"Single price drop.")
            self.actions.pressButton("LowerPrice")
            self.priceAdjustmentTime += 0.5
        elif unsold < 4 * rate:
            TS.print(f"Single price raise.")
            self.actions.pressButton("RaisePrice")
            self.priceAdjustmentTime += 0.5
        else:
            self.priceAdjustmentTime = 5.0

        self.lastPriceAdjustment = TS.now()

    def tick(self):
        self.__adjustPrice()
