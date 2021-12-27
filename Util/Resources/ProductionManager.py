# Class to manage acquisition of drones, factories, solar farms and batteries
from selenium.webdriver.remote.webelement import WebElement
from Webpage.PageState.PageActions import PageActions
from Webpage.PageState.PageInfo import PageInfo
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

    def __le__(self, other) -> bool:
        return self == other or self < other


class ProductionManager():
    # itemButtons = {Item.Factory: "BuyFactory", Item.Harvester: "BuyHarvester",
    #                Item.Wire: "BuyWire", Item.Solar: "BuySolar", Item.Battery: "BuyBattery"}
    buttons = {
        Item.Factory: "BuyFactory",
        Item.Harvester: "BuyHarvester",  # , "BuyHarvesterx10", "BuyHarvesterx100", "BuyHarvesterx1000"],
        Item.Wire: "BuyWire",  # , "BuyWirex10", "BuyWirex100", "BuyWirex1000"],
        Item.Solar: "BuySolar",  # , "BuySolarx10", "BuySolarx100"],
        Item.Battery: "BuyBattery"}  # , "BuyBatteryx10", "BuyBatteryx100"]}

    power = {Item.Factory: 200, Item.Harvester: 1, Item.Wire: 1}

    def __enoughPower(self, item: Item, amount: int = 1) -> bool:
        powerRequired = amount * ProductionManager.power[item]
        availPower = self.freePower()
        return availPower - powerRequired > 0

    # TODO: Perhaps enable these again
    # def __getHighest(self, item: Item) -> Tuple[str, int]:
    #     buttonList = ProductionManager.buttons[item]
    #     highestButton = None
    #     for button in buttonList[::-1]:
    #         if self.actions.isEnabled(button):
    #             highestButton = button
    #             break

    #     if not highestButton:
    #         return (None, 0)

    #     amount = 10 ** highestButton.count("0")  # Bit crude, but works for all cases here
    #     if item in [Item.Factory, Item.Harvester, Item.Wire]:
    #         # TS.print(f"Check for power.")
    #         if not self.__enoughPower(item, amount):
    #             highestButton, amount = self.__getHighest(Item.Solar)
    #             # TS.print(f"Not enough power, buying {amount} solar farms instead.")

    #     return (highestButton, amount)

    def __buy(self, item: Item) -> bool:
        # Note: 1000 Battery Towers are needed to finish Phase 2
        # TODO: create a nice way to buy higher quantities
        # --> If 100 is enabled --> buy 10, if 1k is enabled, buy 100

        button = ProductionManager.buttons[item]
        amount = 1

        if not button or not self.actions.isEnabled(button):
            return False

        self.actions.pressButton(button)
        self.itemCount[item] += amount
        TS.print(
            f"Bought {button}, current count is {self.itemCount[item]}. Previous count was increased with {amount}.")
        self.nextItem = None

        return True

    def __firstBuy(self):
        self.__buy(Item.Solar)
        self.__buy(Item.Harvester)
        self.__buy(Item.Wire)
        self.__buy(Item.Factory)
        time.sleep(1)

    def __init__(self, pageInfo: PageInfo, pageAction: PageActions) -> None:
        self.info = pageInfo
        self.actions = pageAction
        self.ratio = 1.625  # Production speed Harvester vs Wire is 1.625 : 1
        self.itemCount = {item: 0 for item in Item}
        self.freePower = lambda: self.itemCount[Item.Solar] * 50 - (
            self.itemCount[Item.Factory] * 200 + self.itemCount[Item.Harvester] + self.itemCount[Item.Wire])
        self.lastBuy = Config.get("Gamestart")
        self.__firstBuy()
        self.nextItem = None
        self.lastProdValue = _ClipValue(self.info.get("FactoryClipsPerSec"))
        self.lastValueMoment = TS.now()

        # Factories: 200 power, drones: 1 power

    def __determineNext(self) -> Item:
        wirePerSec = _ClipValue(self.info.get("WirePerSec"))
        clipsPerSec = _ClipValue(self.info.get("FactoryClipsPerSec"))
        clipsPerSec.value *= 1.1  # Slight inflation of the value
        # FIXME: could cause slight problems when increasing 999 to 1k+, as its magitude will remain unchanged

        # Only allow factories if their production rate hasn't changed for at least 3 sec and is below clips production
        # TODO: Move to config
        if TS.delta(self.lastValueMoment) > 3 and clipsPerSec < wirePerSec:
            return Item.Factory

        # TODO: Temporarily modify the ratio slightly if small reserves accrue
        ratio = float(float(self.itemCount[Item.Wire] / self.itemCount[Item.Harvester]))
        return Item.Harvester if ratio > self.ratio else Item.Wire

    def __buyNext(self) -> None:
        if not self.nextItem:
            self.nextItem = self.__determineNext()

        if self.nextItem in ProductionManager.power and not self.__enoughPower(self.nextItem):
            self.nextItem = Item.Solar

        if self.nextItem == Item.Factory and TS.delta(self.lastBuy) < 3:

            # FIXME: Still causes problems: buying new Wireproduction just before the deadline changes state
            # Perhaps only buy Factories if value is stable for ~3 sec and lower than clipper prod.

            self.nextItem = None
            return

        if self.__buy(self.nextItem) and self.nextItem == Item.Factory:
            self.lastBuy = TS.now()

    def __checkProductionStability(self):
        clipsPerSec = _ClipValue(self.info.get("FactoryClipsPerSec"))
        if clipsPerSec != self.lastProdValue:
            self.lastProdValue = clipsPerSec
            self.lastValueMoment = TS.now()

    def tick(self):
        self.__checkProductionStability()
        self.__buyNext()
