from Webpage.PageState.PageActions import PageActions
from Webpage.PageState.PageInfo import PageInfo
from Util.Timestamp import Timestamp as TS


class PriceWatcher():
    def __init__(self, pageInfo: PageInfo, pageActions: PageActions) -> None:
        self.info = pageInfo
        self.actions = pageActions
        self.priceAdjustmentTime = 5.0
        self.lastPriceAdjustment = TS.now()
        pass

    def __adjustPrice(self):
        # Only adjust price once every x sec.
        if TS.delta(self.lastPriceAdjustment) < self.priceAdjustmentTime:
            return

        rate, unsold = [self.info.getInt(field) for field in ("ClipsPerSec", "Unsold")]

        if rate < 40:
            # Prevents stuttering at low rates
            return

        # OPT: Optimize to lose a bit less money on the lower side, this slows down buying early clippers
        # OPT: Maybe couple Market Demand with production speed instead
        if unsold > 8 * rate:
            self.actions.pressButton("LowerPrice")
            self.priceAdjustmentTime += 0.5
        elif unsold < 4 * rate:
            self.actions.pressButton("RaisePrice")
            self.priceAdjustmentTime += 0.5
        else:
            self.priceAdjustmentTime = 5.0

        self.lastPriceAdjustment = TS.now()

    def tick(self):
        self.__adjustPrice()
