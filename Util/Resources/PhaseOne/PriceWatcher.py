from Webpage.PageState.PageActions import PageActions
from Webpage.PageState.PageInfo import PageInfo
from Util.Timestamp import Timestamp as TS
from Util.Files.Config import Config
from Util.Listener import Event, Listener


class PriceWatcher():
    """Manages the pricing of the paperclips."""
    __DEFAULT_ADJUST_INTERVAL = 1.5

    def __revTrackerAcquired(self, _: str) -> None:
        """Callback for when the RevTracker project is bought."""
        self.revTrackerOnline = True

    def __fullMonopolyAcquired(self, _: str) -> None:
        """Pre-emptively increases the price after large increase of public demand when acquiring Full Monopoly."""

        # $0.51 cent seems a stable starting point.
        TS.print(f"Full monopoly acquired. Increasing current price from [{self.currPrice}] to [51] cent.")
        if self.currPrice >= 51:
            return

        self.__up(51 - self.currPrice)

    def __up(self, amount: int = 1):
        """Increases the price of paperclips."""
        for _ in range(amount):
            self.actions.pressButton("RaisePrice")
            self.currPrice += 1

        self.lastPriceChange = TS.now()

    def __down(self, amount: int = 1):
        """Lowers the price of paperclips if possible, otherwise ignores the attempt."""
        priceChanged = False
        minValue = 1 if self.revTrackerOnline else 2  # Price should never drop to 1 early game
        for _ in range(amount):
            if self.currPrice > minValue:
                self.actions.pressButton("LowerPrice")
                self.currPrice -= 1
                priceChanged = True
            else:
                break
        if priceChanged:
            self.lastPriceChange = TS.now()

    def __init__(self, pageInfo: PageInfo, pageActions: PageActions) -> None:
        self.info = pageInfo
        self.actions = pageActions
        self.lastPriceChange = TS.now()
        self.firstTime = True
        self.revTrackerOnline = False

        self.currPrice = 25
        self.adjustmentInterval = PriceWatcher.__DEFAULT_ADJUST_INTERVAL

        self.prevProdRate = 73  # About max of what the autoclicker is able to reach.
        self.prevInventory = 0
        self.prevTime = TS.now()

        # $0.03 is a decent starting price.
        for _ in range(22):
            self.__down()

        Listener.listenTo(Event.BuyProject, self.__revTrackerAcquired, "RevTracker", True)
        Listener.listenTo(Event.BuyProject, self.__fullMonopolyAcquired, "Full Monopoly", True)

    def __adjustPrice(self) -> None:
        """Calculates price adjustment based on production vs sales."""

        if self.firstTime and TS.delta(Config.get("Gamestart")) < 15:
            # Delay adjusting the price for a bit at the start of the game.
            return
        else:
            self.firstTime = False

        if TS.delta(self.lastPriceChange) < self.adjustmentInterval:
            # Don't change the price too often, allows the averages to balance out for a bit.
            return

        soldPerSec = self.info.getInt("ClipsSoldPerSec") if self.revTrackerOnline else self.__getSellRate()
        madePerSec = self.info.getInt("ClipsPerSec")
        inventory = self.info.getInt("Unsold")

        if inventory < madePerSec:
            # Emergency increase
            self.__up()
            self.adjustmentInterval = 0.5
        else:
            self.adjustmentInterval = PriceWatcher.__DEFAULT_ADJUST_INTERVAL

        if inventory < 6 * madePerSec and madePerSec > soldPerSec:
            # Inventory is low, but it's growing.
            return
        elif inventory > 12 * madePerSec and soldPerSec > madePerSec:
            # Inventory is high, but it's shrinking.
            return

        if soldPerSec == madePerSec:
            # Absolutely perfect, although it's never gonna happen.
            return

        if soldPerSec > madePerSec:
            self.__up()
        else:
            self.__down()

    def __getSellRate(self):
        """Calculate sell rates from current and previous inventory values."""
        timeElapsed = TS.delta(self.prevTime)
        currProdRate = self.info.getInt("ClipsPerSec")

        # Average between past and current production rates
        avgProducedClips = timeElapsed * (currProdRate + self.prevProdRate) / 2
        self.prevProdRate = currProdRate
        clipsSold = self.prevInventory + avgProducedClips - self.info.getInt("Unsold")

        return int(clipsSold / timeElapsed)

    def tick(self) -> None:
        self.__adjustPrice()
