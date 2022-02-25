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
    magnitudes = {"zero": -1, "million": 0, "billion": 1, "trillion": 2, "quadrillion": 3, "quintillion": 4,
                  "sextillion": 5, "septillion": 6, "octillion": 7, "nonillion": 8, "decillion": 9}

    inverse_magnitudes = {}

    def __init__(self, value: WebElement) -> None:
        if value.text != '0':
            number, magnitude = value.text.split()
        else:
            number = 0
            magnitude = "zero"

        self.value = float(number)
        self.magnitude = _ClipValue.magnitudes[magnitude]

    def __lt__(self, other) -> bool:
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
        if self.value > 1_000.0 and (self.magnitude + 1) in _ClipValue.inverse_magnitudes:
            self.value /= 1_000.0
            self.magnitude += 1

        return self

    def zero(self) -> bool:
        return self.value == 0 and self.magnitude == -1

# TODO: the buy() functions could probably use quite a bit of refactoring


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

    def __swarmAcquired(self, _: str) -> None:
        self.actions.setSlideValue("SwarmSlider", 170)
        # TODO: Probably going to need a seperate swarm balancer
        # Push the slider more to think when wire/s >> clips/s
        # 120k ops required to finish the phase

    def __supplyChainAcquired(self, _: str) -> None:
        self.supplyChainBought = True

    def __triggerPlanetaryConsumption(self):
        self.actions.setSlideValue("SwarmSlider", 10)
        self.consumeAll = True
        TS.print("Triggered planetary consumption!")

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
        _ClipValue.inverse_magnitudes = {value: key for (key, value) in _ClipValue.magnitudes.items()}

        self.droneRatio = 1.625  # Production speed Harvester vs Wire is 1.625 : 1
        self.itemCount = {item: 0 for item in Item}
        self.freePower = lambda: self.itemCount[Item.Solar] * 50 - (
            self.itemCount[Item.Factory] * 200 + self.itemCount[Item.Harvester] + self.itemCount[Item.Wire])
        self.__firstBuy()
        self.nextItem = None
        self.momentum = False
        self.lastProdValue = _ClipValue(self.info.get("FactoryClipsPerSec"))
        self.lastValueMoment = TS.now()
        self.initSwarm = True
        self.supplyChainBought = False
        self.consumeAll = False
        self.dronesDissed = False
        self.killPlanetaryConsumption = False

        Listener.listenTo(Event.BuyProject, self.__momentumAcquired, lambda project: project == "Momentum", True)
        Listener.listenTo(Event.BuyProject, self.__swarmAcquired, lambda project: project == "Swarm Computing", True)
        Listener.listenTo(Event.BuyProject, self.__supplyChainAcquired,
                          lambda project: project == "Supply Chain", True)

    def __pressBuy(self, item: Item, amount: int = None) -> None:
        button = ClipSpender.buttons[item]

        if amount:
            button += f"x{amount}"
        else:
            amount = 1

        if not self.actions.isEnabled(button):
            return

        self.actions.pressButton(button)
        self.itemCount[item] += amount
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

            # Make one safe attempt and try to fastbuy the rest
            if not self.__buy(nextDroneButton()):
                return False
            amount -= 1

            # This will still be safe if no higher magnitude button is enabled
            if not self.__fastBuy(amount):
                return False

        return True

    def __buy(self, item: Item) -> bool:
        # Note: 1000 Battery Towers are needed to finish Phase 2
        # TODO: Maybe make a buysafe that checks for power consumption first

        button = ClipSpender.buttons[item]

        if not button or not self.actions.isEnabled(button):
            return False

        self.__pressBuy(item)
        return True

    def __determineNext(self) -> Item:

        if self.consumeAll:
            return Item.Harvester

        # Only allow factories if their production rate is stable for a few seconds
        # It also limits buying a factory to every couple of seconds
        if TS.delta(self.lastValueMoment) > float(Config.get("FactoryStableTime")):
            clipsPerSec = _ClipValue(self.info.get("FactoryClipsPerSec"))
            wirePersec = _ClipValue(self.info.get("WirePerSec"))
            buffer = 1 if not self.momentum else 1.25
            if clipsPerSec * buffer < wirePersec:
                return Item.Factory

        return Item.Harvester  # Doesn't matter which drone you return, handled seperately

    def buyLarge(self) -> None:
        # Always buy second highest (?)
        highestEnabled = None
        droneButton = ClipSpender.buttons[self.nextItem]
        for magnitude in [1000, 100, 10]:
            if self.freePower() >= magnitude and self.actions.isEnabled("".join([droneButton, f"x{magnitude}"])):
                highestEnabled = magnitude
                break

        if self.nextItem == Item.Harvester:
            currRatio = lambda: float(self.itemCount[Item.Wire]) / float(self.itemCount[Item.Harvester])
            self.nextItem = Item.Harvester if currRatio() > self.droneRatio else Item.Wire

        self.__pressBuy(self.nextItem, highestEnabled)

    def buySolar(self) -> None:
        # Always buy highest amount possible (?)
        highestEnabled = None
        solarButton = ClipSpender.buttons[self.nextItem]
        for magnitude in [100, 10]:
            if self.actions.isEnabled("".join([solarButton, f"x{magnitude}"])):
                highestEnabled = magnitude
                break

        self.__pressBuy(self.nextItem, highestEnabled)

    def __solarBought(self) -> bool:
        if self.nextItem in ClipSpender.power and not self.freePower() - ClipSpender.power[self.nextItem] > 0:
            self.nextItem = Item.Solar
            self.buySolar()
            return True
        return False

    def __buyNext(self) -> None:
        if not self.supplyChainBought and self.itemCount[Item.Factory] >= 50:
            # Saving up clips to acquire self-correcting Supply Chain
            return

        if self.itemCount[Item.Factory] >= int(Config.get("ConsumePlanetFactoryThreshold")):
            self.__triggerPlanetaryConsumption()

        if not self.nextItem:
            self.nextItem = self.__determineNext()

        if self.__solarBought():
            return

        if self.nextItem in [Item.Harvester, Item.Wire]:
            self.buyLarge()
            return

        if self.__buy(self.nextItem) and self.nextItem == Item.Factory:
            self.lastValueMoment = TS.now()

    def __checkProductionStability(self):
        """As long as momentum isn't acquired, checks if production has been stable for a couple of seconds. this allows production to stabilize for a bit after buying an additional factory and prevents overbuying them."""

        if self.momentum:
            # No use in checking stability if momentum is acquired, because it will increase constantly
            return

        clipsPerSec = _ClipValue(self.info.get("FactoryClipsPerSec"))
        if clipsPerSec != self.lastProdValue:
            self.lastProdValue = clipsPerSec
            self.lastValueMoment = TS.now()

    def __consumePlanet(self):
        if self.killPlanetaryConsumption:
            return

        # Finish out the phase
        self.nextItem = Item.Harvester

        if self.__solarBought():
            return

        if self.freePower() > 200 and _ClipValue(
                self.info.get("FactoryClipsPerSec")) > _ClipValue(
                self.info.get("FactoryCost")):
            self.__buy(Item.Factory)
            return

        if not self.dronesDissed:
            if self.info.get("AvailMatter").text == "0":
                self.actions.pressButton("DissHarvester")

                if self.info.get("AcquiredMatter").text == "0":
                    self.actions.pressButton("DissWire")
                    self.dronesDissed = True
                else:
                    # No more available matter, but still acquired matter left.
                    # Choosing a wire drone over a harvester skips the autobalancer
                    self.nextItem = Item.Wire
                    self.buyLarge()

            else:
                # Still matter available
                self.nextItem = Item.Harvester
                self.buyLarge()
            return

        if self.itemCount[Item.Battery] < 1_000:
            self.__pressBuy(Item.Battery, 100)
            return

        # OPT: Technically the cutoff point could be higher. There's 6 oct clips and you only need five. This does require dissasembling your factories on the right moment.
        if self.info.get("WireStock").text != '0':
            self.__buy(Item.Factory)
        else:
            self.actions.pressButton("DissFactory")
            self.killPlanetaryConsumption = True
            # This should more or less trigger the next phase

    def tick(self):
        if not self.consumeAll:
            # Regular course of second phase
            # TODO: Entertain the swarm when necesarry
            self.__checkProductionStability()
            self.__buyNext()
        else:
            # Last part, exhausting planetary supplies
            self.__consumePlanet()
