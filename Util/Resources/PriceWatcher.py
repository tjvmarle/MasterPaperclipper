import time
from multiprocessing.dummy import Process
from Webpage.PageState.PageActions import PageActions
from Webpage.PageState.PageInfo import PageInfo
from Util.Timestamp import Timestamp as TS
from Util.Files.Config import Config
from Util.Listener import Event, Listener


class PriceWatcher():
    def activateRevTracker(self) -> None:
        time.sleep(0.75)
        self.revTracker = True

    def revTrackerAcquired(self, project: str) -> None:
        thread = Process(target=self.activateRevTracker)
        thread.start()

    def kill(self, _: str) -> None:
        self.Alive = False

    def __init__(self, pageInfo: PageInfo, pageActions: PageActions) -> None:
        self.info = pageInfo
        self.actions = pageActions
        self.lastPriceAdjustment = TS.now()
        self.demand = self.info.getInt("Demand")
        self.revTracker = False
        self.Alive = True
        self.firstTime = True

        self.adjustmentInterval = 2

        Listener.listenTo(Event.BuyProject, self.revTrackerAcquired, lambda project: project == "RevTracker", True)
        Listener.listenTo(Event.BuyProject, self.kill, lambda project: project == "Release the HypnoDrones", True)

        for _ in range(22):
            self.actions.pressButton("LowerPrice")

    def __adjustPrice(self):
        # FIXME: This method needs a major overhaul. The more I fix it, the more it breaks.

        if self.firstTime and TS.delta(Config.get("Gamestart")) < 10:
            return
        else:
            self.firstTime = False

        rate = self.info.getInt("ClipsPerSec")

        if rate == 0:
            # Out of wire
            return

        lastAdjustment = TS.delta(self.lastPriceAdjustment)

        if lastAdjustment < self.adjustmentInterval:
            return

        unsold = self.info.getInt("Unsold")

        if unsold < rate:
            # Emergency increase
            self.actions.pressButton("RaisePrice")
            self.adjustmentInterval = 0.5
            return
        else:
            self.adjustmentInterval = 2
            if lastAdjustment < self.adjustmentInterval:
                return

        if unsold > 10 * rate:
            self.actions.pressButton("LowerPrice")
            # OPT: enabled status can be determined from internal tracking of the price
            if self.actions.isEnabled("LowerPrice"):
                self.actions.pressButton("LowerPrice")
        elif unsold > 6 * rate:
            self.actions.pressButton("LowerPrice")
        elif unsold < 3 * rate:
            self.actions.pressButton("RaisePrice")

        self.lastPriceAdjustment = TS.now()

        return

        if rate < 10:
            rate = 10

        # FIXME: This doesn't work with low stock
        # if self.revTracker and lastAdjustment > 5:
        #     self.actions.pressButton("RaisePrice" if self.info.getInt("ClipsSoldPerSec") > rate else "LowerPrice")
        #     return

        if self.revTracker:
            # This is probably slow to react after large changes
            if unsold > 4 * rate and lastAdjustment > 2:
                self.actions.pressButton("LowerPrice")
            elif unsold < 2 * rate and lastAdjustment > 2:
                self.actions.pressButton("RaisePrice")
            return

        # FIXME: This is garbage
        demand = self.info.getInt("Demand")
        while rate > 0 and demand > 5 * rate:  # Emergency handling for large changes in marketing
            self.actions.pressButton("RaisePrice")
            demand = self.info.getInt("Demand")

        if lastAdjustment > 0.25 and unsold < rate:  # Emergency handling for low stock
            self.lastPriceAdjustment = TS.now()
            self.actions.pressButton("RaisePrice")
            return

        if lastAdjustment > 0.25 and unsold > 20 * rate:  # Emergency handling for high stock
            self.lastPriceAdjustment = TS.now()
            self.actions.pressButton("LowerPrice")
            return

        if lastAdjustment < self.priceAdjustmentTime:
            return

    def tick(self):
        if self.Alive:
            self.__adjustPrice()
