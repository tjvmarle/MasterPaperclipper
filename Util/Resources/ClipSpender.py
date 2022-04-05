# Class to manage acquisition of drones, factories, solar farms and batteries
from selenium.webdriver.remote.webelement import WebElement
from Webpage.PageState.PageActions import PageActions
from Webpage.PageState.PageInfo import PageInfo
from Util.Listener import Event, Listener
from Util.Timestamp import Timestamp as TS
from Util.Files.Config import Config
from enum import Enum, auto
from multiprocessing import Lock
import time


class Item(Enum):
    Factory = auto()
    Harvester = auto()
    Wire = auto()
    Solar = auto()
    Battery = auto()


class _ClipValue():
    magnitudes = {"zero": -1, "million": 0, "billion": 1, "trillion": 2, "quadrillion": 3, "quintillion": 4,
                  "sextillion": 5, "septillion": 6, "octillion": 7, "nonillion": 8, "decillion": 9}

    inverse_magnitudes = {}

    def __init__(self, value: WebElement) -> None:
        value = value.text

        if " " not in value:
            number = value
            magnitude = "zero"
        else:
            number, magnitude = value.split(" ")

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


# Because multithreading only has benefits, right?
closeOutMutex = Lock()


class ClipSpender():
    # TODO: the buy() functions could probably use quite a bit of refactoring

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

    def __init__(self, pageInfo: PageInfo, pageAction: PageActions) -> None:
        self.info = pageInfo
        self.actions = pageAction

        # For some stupid reason this doesn't work in-class
        _ClipValue.inverse_magnitudes = {value: key for (key, value) in _ClipValue.magnitudes.items()}

        self.droneRatio = 1.625  # Production speed Harvester vs Wire is 1.625 : 1
        self.itemCount = {item: 0 for item in Item}
        self.freePower = lambda: self.itemCount[Item.Solar] * 50 - (
            self.itemCount[Item.Factory] * 200 + self.itemCount[Item.Harvester] + self.itemCount[Item.Wire])
        self.nextItem = None
        self.momentum = False
        self.lastProdValue = _ClipValue(self.info.get("FactoryClipsPerSec"))
        self.lastValueMoment = TS.now()
        self.initSwarm = True
        self.supplyChainBought = False
        self.consumeAll = False
        self.dronesDissed = False
        self.killPlanetaryConsumption = False
        self.phaseTwoFullyInitialized = False

        Listener.listenTo(Event.BuyProject, self.__momentumAcquired, "Momentum", True)
        Listener.listenTo(Event.BuyProject, self.__swarmAcquired, "Swarm Computing", True)
        Listener.listenTo(Event.BuyProject, self.__supplyChainAcquired, "Supply Chain", True)
        Listener.listenTo(Event.BuyProject, self.__delayedInitialization, "Clip Factories", True)

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
        # TODO: Maybe make a buysafe that checks for power consumption first

        button = ClipSpender.buttons[item]

        if not button or not self.actions.isEnabled(button):
            return False

        self.__pressBuy(item)
        return True

    def __determineNext(self) -> Item:
        # Prevents running out of clips before any factory is bought, softlocking the script.
        if self.itemCount[Item.Factory] == 0:
            return Item.Factory

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
            currRatio = lambda: self.droneRatio + 1

            # Prevents division by zero
            if self.itemCount[Item.Harvester] != 0:
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

    def __maximizeSwarm(self):
        with closeOutMutex:
            self.actions.setThreadClickerActivity(False)

            highestDroneCount = max(self.info.getInt("HarvesterCount"), self.info.getInt("WireCount"))

            # The end result should be: 5,832,402/5,832,403
            for _ in range(5872 - int(highestDroneCount / 1000)):
                self.actions.pressButton("BuyHarvesterx1000")
                self.actions.pressButton("BuyWirex1000")
                # TODO: Check yomi  through main tread and abort if it exceeds the limits

            while(self.actions.isEnabled("BuyHarvester")):
                self.nextItem = Item.Harvester
                self.buyLarge()

            self.actions.setThreadClickerActivity(True)

    def __prepareThirdPhase(self):
        """Gathers additional yomi and Swarm Gifts before starting the third phase."""
        self.droneRatio = 1
        self.actions.setThreadClickerActivity(False)  # Don't need these for now.

        # Start buying drones while factories are still converting remaining wire to clips.
        if self.info.get("WireStock").text != '0':
            self.nextItem = Item.Harvester
            self.buyLarge()
            return

        self.actions.pressButton("DissFactory")
        self.actions.pressButton("DissSolar")

        # A single Solar is required or else the swarm will fall asleep, acquiring more seems to make no difference
        self.actions.pressButton("BuySolar")
        self.itemCount[Item.Solar] = 10_000_000  # Ugly, but works for now

        TS.setTimer(0, self.__maximizeSwarm)  # No delay required, just run a seperate thread

    def entertainSwarm(self) -> None:
        if self.actions.isVisible("EntertainSwarm") and self.actions.isEnabled("EntertainSwarm"):
            self.actions.pressButton("EntertainSwarm")

    def closeOutSecondPhase(self) -> None:
        if self.itemCount[Item.Battery] >= 1_000:
            return

        # If __maximizeSwarm() is running right now we skip this function for the moment.
        if not closeOutMutex.acquire(False):
            TS.print("Mutex taken. Skipping closeOutSecondPhase() for now.")
            return

        TS.print("Closing out the second Phase.")

        self.actions.pressButton("DissHarvester")
        self.itemCount[Item.Harvester] = 0

        self.actions.pressButton("DissWire")
        self.itemCount[Item.Wire] = 0

        for _ in range(10):
            self.__pressBuy(Item.Battery, 100)
            self.__pressBuy(Item.Solar, 100)

        # Because charing the batteries is relatively slow.
        for _ in range(390):  # Might be a bit on the high side.
            self.__pressBuy(Item.Solar, 100)

    def __consumePlanet(self):
        self.entertainSwarm()

        if self.killPlanetaryConsumption:
            if self.info.getInt("Yomi") > 351_658:  # Yomi cost for 20 Probe Trust in Phase 3.
                TS.print(" 2: Enough Yomi available at first attempt, closing out the second phase.")
                self.closeOutSecondPhase()
            else:
                TS.print(" 2: Not enough Yomi, waiting a little bit before closing out the second phase.")
                self.__prepareThirdPhase()

            return

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
                self.itemCount[Item.Harvester] = 0

                if self.info.get("AcquiredMatter").text == "0":
                    self.actions.pressButton("DissWire")
                    self.itemCount[Item.Wire] = 0
                    self.dronesDissed = True
                    self.actions.setSlideValue("SwarmSlider", 200)
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

        # OPT: Technically the cutoff point could be higher. There's 6 oct clips and you only need five. This does require dissasembling your factories on the right moment.
        if self.info.get("WireStock").text != '0' and self.itemCount[Item.Factory] < 200:
            self.__buy(Item.Factory)
            return

        # Nearing the end of second phase
        self.killPlanetaryConsumption = True
        TS.print("Triggering planetary consumption.")

        # FIXME: This isn't right yet. This will trigger at 200 factories and an unconverted planet. __prepareThirdPhase will only run partially if there's still remaining matter/wire and won't trigger again.
        if self.info.getInt("Yomi") > 351_658:  # Yomi cost for 20 Probe Trust in Phase 3.
            TS.print("Enough Yomi available at first attempt, closing out the second phase.")
            self.closeOutSecondPhase()
        else:
            TS.print("Not enough Yomi, waiting a little bit before closing out the second phase.")
            self.__prepareThirdPhase()

    def __delayedInitialization(self, _: str):
        """All the items first need to be acquired through projects. The initialization is needed because clip production otherwise won't start up naturally. This requires dropping performance below 100%."""

        self.__buy(Item.Solar)
        self.__buy(Item.Harvester)
        self.__buy(Item.Wire)
        self.__buy(Item.Factory)

        self.phaseTwoFullyInitialized = True

    def tick(self):
        if not self.phaseTwoFullyInitialized:
            return

        # TODO: refactor this entire class. It's too big and has too many flags/states.
        if not self.consumeAll:
            # Regular course of second phase
            self.entertainSwarm()
            self.__checkProductionStability()
            self.__buyNext()
        else:
            # Last part, exhausting planetary supplies
            self.__consumePlanet()
