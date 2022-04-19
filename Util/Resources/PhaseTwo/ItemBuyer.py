from __future__ import annotations  # Otherwise type hinting a class within itself won't work
from typing import List
from Webpage.PageState.PageActions import PageActions
from Webpage.PageState.PageInfo import PageInfo

from enum import Enum, auto


class Item(Enum):
    Factory = auto()
    Harvester = auto()
    Wire = auto()
    AnyDrone = auto()
    Solar = auto()
    Battery = auto()


class ItemBuyer():
    """Class to handle actually buying the requested items. This requires balancing and calculating optimal strategies 
    between the available buttons."""

    # The base buttons available to actually buy something.
    __buttons = {
        Item.Factory: "BuyFactory",
        Item.Harvester: "BuyHarvester",
        Item.Wire: "BuyWire",
        Item.Solar: "BuySolar",
        Item.Battery: "BuyBattery"}

    # Available sizes to buy a specific item amount
    __itemSizes = {Item.Factory: (1,), Item.Harvester: (1, 10, 100, 1000), Item.Wire: (1, 10, 100, 1000),
                   Item.Solar: (1, 10, 100),  Item.Battery: (1, 10, 100)}

    class __ButtonAmount():
        """Data struct with some coupling between a buttonstring and their integer value."""

        def __init__(self, buttonString: str, buttonValue: int) -> None:
            self.string = buttonString
            self.value = buttonValue

    def __init__(self, pageInfo: PageInfo, pageAction: PageActions) -> None:
        self.info = pageInfo
        self.actions = pageAction

    def buyAmount(self, item: Item, amount: int) -> int:
        """Tries to buy an exact amount of items. Returns the actual amount bought."""

        # TODO: buyList can probably be a generator instead
        buyList = self.__splitAmountToButtonInstances(item, amount)

        totalBought = 0
        for buttonAmount in buyList:
            if not self.actions.isEnabled(buttonAmount.string):
                continue

            self.actions.pressButton(buttonAmount.string)
            totalBought += buttonAmount.value

        return totalBought

    def __splitAmountToButtonInstances(self, item: Item, amount: int) -> List[ItemBuyer.__ButtonAmount]:
        """Splits an item amount into a series of buttonstrings required to buy that amount. E.g. 132 Wiredrones becomes 
        ['BuyWirex100', 'BuyWirex10', 'BuyWirex10', 'BuyWirex10', 'BuyWire', 'BuyWire']."""

        if item == Item.Factory:
            factoryButtonString = ItemBuyer.__buttons[Item.Factory]
            return [ItemBuyer.__ButtonAmount(factoryButtonString, 1) for _ in range(amount)]

        thousands: list[int] = []
        if item == Item.Harvester or item == Item.Harvester:
            rangeVal, amount = divmod(amount, 1000)
            thousands = [1000 for _ in range(rangeVal)]

        rangeVal, amount = divmod(amount, 100)
        hundreds = [100 for _ in range(rangeVal)]

        rangeVal, amount = divmod(amount, 10)
        tens = [10 for _ in range(rangeVal)]

        singles = [1 for _ in range(amount)]

        totalList = thousands + hundreds + tens + singles
        return [self.__itemAmountToButtonAmount(item, instanceAmount) for instanceAmount in totalList]

    def __itemAmountToButtonAmount(self, item: Item, amount: int) -> str:
        """Translates an item and their required amount to the relevant webpage button."""
        if amount not in ItemBuyer.__itemSizes[item]:
            raise NotImplementedError(f"Value [{amount}] is unavailable for item [{item}].")

        buttonBase = ItemBuyer.__buttons[item]
        NewButton = ItemBuyer.__ButtonAmount
        return NewButton(buttonBase, amount) if amount == 1 else NewButton(f"{buttonBase}x{amount}", amount)
