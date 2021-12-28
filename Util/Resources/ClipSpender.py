# Class to manage acquisition of drones, factories, solar farms and batteries
from selenium.webdriver.remote.webelement import WebElement
from Webpage.PageState.PageActions import PageActions, AutoTarget
from Webpage.PageState.PageInfo import PageInfo
from Util.Listener import Event, Listener
from Util.Timestamp import Timestamp as TS
from Util.Files.Config import Config
from enum import Enum
from typing import Tuple
import time


class Item(Enum):
    Factory = 1
    Harvester = 2
    Wire = 3
    Solar = 4
    Battery = 5


class _ClipValue():
    # TODO: Add other magnitudes
    magnitudes = {"million": 0, "billion": 1, "trillion": 2, "qaudrillion": 3, "octillion": 99}
    inv_mag = {}

    def __init__(self, value: WebElement) -> None:
        number, magnitude = value.text.split()
        self.value = float(number)
        self.magnitude = _ClipValue.magnitudes[magnitude]

    def __lt__(self, other):
        if self.magnitude == other.magnitude:
            return self.value < other.value
        else:
            return self.magnitude < other.magnitude

    def __eq__(self, other) -> bool:
        return self.value == other.value and self.magnitude == other.magnitude

    def __ne__(self, other) -> bool:
        return not (self == other)

    def __le__(self, other) -> bool:
        return self == other or self < other

    def __mul__(self, factor: float):
        self.value *= factor
        if self.value > 1_000.0 and (self.magnitude + 1) in _ClipValue.inv_mag:
            self.value /= 1_000.0
            self.magnitude += 1

        return self


class ClipSpender():
    buttons = {
        Item.Factory: "BuyFactory",
        Item.Harvester: "BuyHarvester",
        Item.Wire: "BuyWire",
        Item.Solar: "BuySolar",
        Item.Battery: "BuyBattery"}

    power = {Item.Factory: 200, Item.Harvester: 1, Item.Wire: 1}

    def __momentumAcquired(self, _: str) -> None:
        self.momentum = True

    def __firstBuy(self):
        self.__buy(Item.Solar)
        self.__buy(Item.Harvester)
        self.__buy(Item.Wire)
        self.__buy(Item.Factory)
        time.sleep(1)

    def __init__(self, pageInfo: PageInfo, pageAction: PageActions) -> None:
        self.info = pageInfo
        self.actions = pageAction

        # For some stupid reason this doesn't work in-class
        _ClipValue.inv_mag = {value: key for (key, value) in _ClipValue.magnitudes.items()}

        self.droneRatio = 1.625  # Production speed Harvester vs Wire is 1.625 : 1
        self.itemCount = {item: 0 for item in Item}
        self.freePower = lambda: self.itemCount[Item.Solar] * 50 - (
            self.itemCount[Item.Factory] * 200 + self.itemCount[Item.Harvester] + self.itemCount[Item.Wire])
        self.__firstBuy()
        self.nextItem = None
        self.momentum = False
        self.lastProdValue = _ClipValue(self.info.get("FactoryClipsPerSec"))
        self.lastValueMoment = TS.now()

        Listener.listenTo(Event.BuyProject, self.__momentumAcquired, lambda project: project == "Momentum", True)

    def __pressBuy(self, item: Item) -> None:
        button = ClipSpender.buttons[item]
        self.actions.pressButton(button)
        self.itemCount[item] += 1
        self.nextItem = None

    def __fastBuy(self, amount: int = None) -> bool:
        # For some reason the performance tanks after the first couple of drones are bought. This method is mostly to optimize acquiring the drones in a balanced matter, without checking too often if the required buttons are enabled.

        highestEnabled = None
        wireButton = ClipSpender.buttons[Item.Wire]  # Wire drones should always be higher and thus the limiting factor
        for magnitude in [1000, 100, 10]:
            if self.actions.isEnabled("".join([wireButton, f"x{magnitude}"])):
                highestEnabled = magnitude
                break

        if not highestEnabled:
            if not self.actions.isEnabled(wireButton):
                # Not enough clips for a single drone
                return False
            else:
                highestEnabled = 1

        if not amount:
            # Only buy in small batches, or performance might tank again.
            amount = min(self.freePower(), 2 * highestEnabled)

        if amount == 0:
            return

        currRatio = lambda: float(self.itemCount[Item.Wire]) / float(self.itemCount[Item.Harvester])
        nextDroneButton = lambda: Item.Harvester if currRatio() > self.droneRatio else Item.Wire
        if amount <= highestEnabled:
            # No need to check if button is enabled, it should be for total amount
            for _ in range(amount):
                self.__pressBuy(nextDroneButton())
        else:
            # Only highestEnabled drones can be bought without checking.
            for _ in range(highestEnabled):
                self.__pressBuy(nextDroneButton())
            amount -= highestEnabled

            # Make one safe attemt and try to fastbuy the rest
            if not self.__buy(nextDroneButton()):
                return False
            amount -= 1

            # This will still be safe if no higher magnitude button is enabled
            if not self.__fastBuy(amount):
                return False

        return True

    def __buy(self, item: Item) -> bool:
        # Note: 1000 Battery Towers are needed to finish Phase 2

        button = ClipSpender.buttons[item]

        if not button or not self.actions.isEnabled(button):
            return False

        self.__pressBuy(item)
        return True

    def __determineNext(self) -> Item:

        # Only allow factories if their production rate is stable for a few seconds
        # It also limits buying a factory to every couple of seconds
        if TS.delta(self.lastValueMoment) > float(Config.get("FactoryStableTime")):
            clipsPerSec = _ClipValue(self.info.get("FactoryClipsPerSec"))
            wirePersec = _ClipValue(self.info.get("WirePerSec"))
            buffer = 1 if not self.momentum else 1.25
            if clipsPerSec * buffer < wirePersec:
                return Item.Factory

        return Item.Harvester  # Doesn't matter which drone you return, handled seperately

    def __buyNext(self) -> None:
        if not self.nextItem:
            self.nextItem = self.__determineNext()

        if self.nextItem in ClipSpender.power and not self.freePower() - ClipSpender.power[self.nextItem] > 0:
            self.nextItem = Item.Solar

        if self.nextItem in [Item.Harvester, Item.Wire]:
            self.__fastBuy()
            return

        if self.__buy(self.nextItem) and self.nextItem == Item.Factory:
            self.lastValueMoment = TS.now()

    def __checkProductionStability(self):
        if self.momentum:
            return

        clipsPerSec = _ClipValue(self.info.get("FactoryClipsPerSec"))
        if clipsPerSec != self.lastProdValue:
            self.lastProdValue = clipsPerSec
            self.lastValueMoment = TS.now()

    def tick(self):
        # TODO: Add Swarm Computing slider
        self.__checkProductionStability()
        self.__buyNext()
