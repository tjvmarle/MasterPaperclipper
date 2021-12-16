
import time
from multiprocessing.dummy import Process
from Webpage.PageState.PageActions import PageActions
from Webpage.PageState.PageInfo import PageInfo
from Util.Timestamp import Timestamp as TS
from Util.AcquisitionHandler import AcquisitionHandler


class PriceWatcher():
    def activateRevTracker(self) -> None:
        time.sleep(0.75)
        self.revTracker = True

    def revTrackerAcquired(self, project: str) -> None:
        thread = Process(target=self.activateRevTracker)
        thread.start()

    def __init__(self, pageInfo: PageInfo, pageActions: PageActions) -> None:
        self.info = pageInfo
        self.actions = pageActions
        self.priceAdjustmentTime = 3.0
        self.lastPriceAdjustment = TS.now()
        self.demand = self.info.getInt("Demand")
        self.revTracker = False

        self.projectWatcher = AcquisitionHandler()
        self.projectWatcher.addHandle("RevTracker", self.revTrackerAcquired)

        for _ in range(22):
            self.actions.pressButton("LowerPrice")

    def __adjustPrice(self):
        rate = self.info.getInt("ClipsPerSec")
        if rate < 80:
            rate = 60

        lastAdjustment = TS.delta(self.lastPriceAdjustment)

        # FIXME: This doesn't work with low stock
        # if self.revTracker and lastAdjustment > 5:
        #     self.actions.pressButton("RaisePrice" if self.info.getInt("ClipsSoldPerSec") > rate else "LowerPrice")
        #     return

        unsold = self.info.getInt("Unsold")
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
            # self.info.update("Demand")
            demand = self.info.getInt("Demand")

        if lastAdjustment > 0.25 and unsold < rate:  # Emergency handling for low stock
            self.actions.pressButton("RaisePrice")
            return

        if lastAdjustment > 0.25 and unsold > 20 * rate:  # Emergency handling for high stock
            self.actions.pressButton("LowerPrice")
            return

        if lastAdjustment < self.priceAdjustmentTime:
            return

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
