import math
from Util.Resources.OrderedEnum import OrderedEnum
from Util.Resources.PhaseTwo.ClipValue import ClipValue
from Util.Resources.PhaseTwo.ItemBuyer import Item, ItemBuyer
from Util.Resources.ThreadClicker import ThreadClicker
from Util.Resources.State import StateTracker
from Webpage.PageState.PageActions import PageActions
from Webpage.PageState.PageInfo import PageInfo
from Util.Listener import Event, Listener
from Util.Timestamp import Timestamp as TS
from Util.Files.Config import Config
from enum import Enum, auto
from typing import Tuple


class ClipSpender():
    """Manages acquisition of drones, factories, solar farms and batteries"""

    class States(OrderedEnum):
        """Describes the different states this class goes through while progressing through phase 2."""

        PreStartup = 0              # Buying projects to be able to actually start the phase
        Startup = 1                 # Just building up production
        MomentumBought = 2          # Acquired Momentum project
        SupplyChainBought = 3       # Acquired Supply Chain project - this requires pausing Item acquisition for a while
        PlanetaryConsumption = 4    # Working towards consuming all planetary mass
        PrepareThirdPhase = 5       # Optional state to gather some more Yomi/Gifts before moving to phase three
        FinishSecondPhase = 6       # Switching resources around to acquire Space Exploration

    buttons = {
        Item.Factory: "BuyFactory",
        Item.Harvester: "BuyHarvester",
        Item.Wire: "BuyWire",
        Item.Solar: "BuySolar",
        Item.Battery: "BuyBattery"}

    power = {Item.Factory: 200, Item.Harvester: 1, Item.Wire: 1, Item.AnyDrone: 1}

    def __momentumAcquired(self, _: str) -> None:
        self.currentState.goTo(self.states.MomentumBought)

    def __swarmAcquired(self, _: str) -> None:
        """Sets the slider to a specific value. Production is mostly bottlenecked by factories anyway and increasing 
        Processors and Memory is often more important than higher production."""

        self.actions.setSlideValue("SwarmSlider", 150)
        # TODO: Probably going to need a seperate swarm balancer. Push the slider more to think when wire/s >> clips/s
        # Perhaps try to reach certain drone counts on high production, then switch to Think for a boost in Gifts.

    def __supplyChainAcquired(self, _: str) -> None:
        self.currentState.goTo(self.states.SupplyChainBought)

    def __delayedInitialization(self, _: str):
        """All the items first need to be acquired through projects. The initialization is needed because clip 
        production otherwise won't start up naturally. This requires dropping performance below 100%."""

        self.__buy(Item.Solar, 1)
        self.__buy(Item.Harvester, 1)
        self.__buy(Item.Wire, 1)
        self.__buy(Item.Factory, 1)

        self.currentState.goTo(self.states.Startup)

    def __init__(self, pageInfo: PageInfo, pageAction: PageActions) -> None:
        self.info = pageInfo
        self.actions = pageAction

        # For some stupid reason this doesn't work in-class
        ClipValue.inverse_magnitudes = {value: key for (key, value) in ClipValue.magnitudes.items()}

        self.droneRatio = 1.625  # Production speed Harvester vs Wire is 1.625 : 1
        self.itemCount = {item: 0 for item in Item}
        self.freePower = lambda: self.itemCount[Item.Solar] * 50 - (
            self.itemCount[Item.Factory] * 200 + self.itemCount[Item.Harvester] + self.itemCount[Item.Wire])
        self.lastProdValue = ClipValue(self.info.get("FactoryClipsPerSec"))
        self.lastValueMoment = TS.now()
        self.swarmMaximizer = ClipSpender.ThreadState.Required

        self.currentState = StateTracker([enum for enum in ClipSpender.States])
        self.states = ClipSpender.States
        self.buyer = ItemBuyer(pageInfo, pageAction)

        Listener.listenTo(Event.BuyProject, self.__delayedInitialization, "Clip Factories", True)
        Listener.listenTo(Event.BuyProject, self.__momentumAcquired, "Momentum", True)
        Listener.listenTo(Event.BuyProject, self.__swarmAcquired, "Swarm Computing", True)
        Listener.listenTo(Event.BuyProject, self.__supplyChainAcquired, "Supply Chain", True)

    def __buy(self, item: Item, amount: int) -> None:
        """Buys a specific amount of an item. Keeps track internally of how many items we have acquired so far. Returns
        actual quantity of items bought."""

        bought = self.buyer.buyAmount(item, amount)
        self.itemCount[item] += bought
        return bought

    def __determineNextItemToBuy(self) -> Item:
        """Determines next item to buy. This only considers the majority of the phase where the purpose is to maximize
        your production. Hence, no batteries will be considered for purchase, as those are only required to close out 
        the phase."""

        def powerCheckedItem(item): return item if self.freePower() > ClipSpender.power[item] else Item.Solar

        if self.__factoryProductionIsAllowed():
            return powerCheckedItem(Item.Factory)
        else:
            return powerCheckedItem(Item.AnyDrone)

    def __factoryProductionIsAllowed(self) -> bool:
        """Checks if clip production is capped because of the factory count. Also checks if enough time has elapsed 
        since previous factory acquisition. If the price is cheap, also buy one."""

        if not TS.delta(self.lastValueMoment) > float(Config.get("FactoryStableTime")) \
                and self.itemCount[Item.Factory] < 60:
            # Without the delay the script tends to buy too many at once when a new factory is required.
            return False

        clipsPerSec = ClipValue(self.info.get("FactoryClipsPerSec"))
        wirePersec = ClipValue(self.info.get("WirePerSec"))

        # Because production keeps increasing after Momentum we use a bit of leeway to determine 'stability'
        buffer = 1 if self.currentState.before(self.states.MomentumBought) else 1.15
        return clipsPerSec * buffer < wirePersec or clipsPerSec > ClipValue(self.info.get("FactoryCost")) \
            or self.itemCount[Item.Factory] > 60

    def __buyNextItem(self) -> None:
        """Buys the next objective. Could be a factory, drone or solar farm. Batteries not included."""

        if self.currentState.before(self.states.SupplyChainBought) and self.itemCount[Item.Factory] >= 50:
            # Saving up clips to acquire self-correcting Supply Chain
            return

        nextItem = self.__determineNextItemToBuy()

        if nextItem == Item.Factory and self.__buy(Item.Factory, 1) > 0:
            self.lastValueMoment = TS.now()

        elif nextItem == Item.Solar:
            self.__buy(Item.Solar, self.__getHighestEnabled(Item.Solar))

        elif nextItem == Item.AnyDrone:
            # The drone amount is capped either by available power or the enabled Harvester button, since we'll usually
            # have fewer Harvesters than WireDrones.
            maxDrones = self.__getHighestEnabled(Item.Harvester)

            if maxDrones == 1000 and self.itemCount[Item.Harvester] + self.itemCount[Item.Wire] > 10_000:
                # If the 1k button is enabled and drone count is relatively high, try to buy more than 1k drones.
                maxDrones = ((self.itemCount[Item.Harvester] + self.itemCount[Item.Wire]) // 5000) * 1000

            droneAmount = min(self.freePower(), maxDrones)
            harvesterDrones, wireDrones = self.__getDroneBalance(droneAmount)
            self.__buy(Item.Harvester, harvesterDrones)
            self.__buy(Item.Wire, wireDrones)

    def __getHighestEnabled(self, item: Item) -> int:
        """Returns the value of the highest button that is enabled for the requested Item."""
        buttonRange = [100, 10]

        if item in [Item.Harvester, Item.Wire]:
            buttonRange = [1000, ] + buttonRange

        buttonString = ClipSpender.buttons[item]
        for magnitude in buttonRange:
            if self.actions.isEnabled(f"{buttonString}x{magnitude}"):
                return magnitude

        return 1 if self.actions.isEnabled(buttonString) else 0

    def __getDroneBalance(self, requiredDrones: int) -> Tuple[int, int]:
        """Determine the distribution between Harvester and Wire drones to acquire."""
        newTotalDrones = self.itemCount[Item.Harvester] + self.itemCount[Item.Wire] + requiredDrones
        newIdealHarvesterCount = math.ceil(newTotalDrones - newTotalDrones / self.droneRatio)
        newIdealWireCount = math.floor(newTotalDrones / self.droneRatio)

        def clamp(value, lower, upper): return max(lower, min(value, upper))
        requiredHarvesters = clamp(newIdealHarvesterCount - self.itemCount[Item.Harvester], 0, requiredDrones)
        requiredWire = clamp(newIdealWireCount - self.itemCount[Item.Wire], 0, requiredDrones)

        return (requiredHarvesters, requiredWire)

    def __checkProductionStability(self):
        """As long as momentum isn't acquired, checks if production has been stable for a couple of seconds. This allows
         production to stabilize for a bit after buying an additional factory and prevents overbuying them."""

        if self.currentState.atLeast(self.states.MomentumBought):
            # No use in checking stability if momentum is acquired, because it will increase constantly.
            return

        clipsPerSec = ClipValue(self.info.get("FactoryClipsPerSec"))
        if clipsPerSec != self.lastProdValue:
            # If production changed since last moment, that means Factories are not capping the output. Update the
            # lastValueMoment to represent that.
            self.lastProdValue = clipsPerSec
            self.lastValueMoment = TS.now()

    class ThreadState(Enum):
        """Just a bit of between-threads-communication. Allows the maximizer to break off early."""

        Required = auto()
        Running = auto()
        NotRequired = auto()
        Finished = auto()

    def __maximizeSwarm(self):
        """Maximizes drone count"""
        with ThreadClicker.Disabled():

            highestDroneCount = max(self.info.getInt("HarvesterCount"), self.info.getInt("WireCount"))

            # The end result should be: 5,832,402/5,832,403
            for _ in range(5872 - int(highestDroneCount / 1000)):
                self.__buy(Item.Harvester, 1000)
                self.__buy(Item.Wire, 1000)

                if self.swarmMaximizer == ClipSpender.ThreadState.NotRequired:
                    break

        self.swarmMaximizer == ClipSpender.ThreadState.Finished

    def __prepareThirdPhase(self):
        """Gathers additional yomi and Swarm Gifts before starting the third phase."""

        if self.itemCount[Item.Solar] != 1:
            # We only need a single solar farm to allow Gifts to be generated.
            self.actions.pressButton("DissSolar")
            self.__buy(Item.Solar, 1)

        if self.swarmMaximizer != ClipSpender.ThreadState.Required:
            return

        # First equalize drone count.
        harvesterCount = self.itemCount[Item.Harvester]
        wireCount = self.itemCount[Item.Wire]
        if harvesterCount != wireCount:
            item = Item.Harvester if harvesterCount < wireCount else Item.Wire
            self.__buy(item, abs(harvesterCount - wireCount))

        self.swarmMaximizer = ClipSpender.ThreadState.Running
        TS.setTimer(0, "SwarmMaximizer", self.__maximizeSwarm)  # No delay required, just run a seperate thread

    def __closeOutSecondPhase(self) -> None:
        """Prepares resources to allow for acquisition of the Space Exploration project."""

        if self.itemCount[Item.Battery] >= 1_000:
            return

        TS.print("Closing out second phase.")

        self.actions.pressButton("DissHarvester")
        self.itemCount[Item.Harvester] = 0

        self.actions.pressButton("DissWire")
        self.itemCount[Item.Wire] = 0

        self.actions.pressButton("DissFactory")
        self.itemCount[Item.Factory] = 0

        self.actions.pressButton("DissSolar")
        self.itemCount[Item.Solar] = 0

        with ThreadClicker.Disabled():
            for _ in range(10):
                self.__buy(Item.Battery, 100)
                self.__buy(Item.Solar, 100)

            # Because charing the batteries is relatively slow.
            for _ in range(390):  # Might be a bit on the high side.
                self.__buy(Item.Solar, 100)

    def __consumePlanet(self):
        """Maximizes drone count while running at full power to convert the entire planet."""

        # TODO: Perhaps change this into a loop that runs for a max amount of iterations buying many solars and drones.
        if self.freePower() < 10_000:
            self.__buy(Item.Solar, self.__getHighestEnabled(Item.Solar))
            return

        harvesterDrones, wireDrones = self.__getDroneBalance(10_000)
        self.__buy(Item.Harvester, harvesterDrones)
        self.__buy(Item.Wire, wireDrones)

        if self.info.get("WireStock").text != "0" or self.info.get("AcquiredMatter").text != "0" \
                or self.info.get("AvailMatter").text != "0":
            return

        # When everything is converted, check if we can move to 3rd phase or have to prepare a bit more.
        self.actions.pressButton("DissFactory")

        # Minimum requirements to start third phase. Required Yomi is good for 18 Trust.
        if self.info.getInt("Yomi") > 351_158 and self.info.getInt("Processors") >= 110 \
                and self.info.getInt("Memory") >= 110:
            self.currentState.goTo(self.states.FinishSecondPhase)
        else:
            # Collect some more Yomi and Swarm gifts.
            self.actions.setSlideValue("SwarmSlider", 200)
            self.currentState.goTo(self.states.PrepareThirdPhase)

    def tick(self) -> None:
        if self.currentState.before(self.states.Startup):
            # Not all Items available yet.
            return

        elif self.currentState.before(self.states.PlanetaryConsumption):
            # Regular course of second phase.
            self.__checkProductionStability()
            self.__buyNextItem()

            # We run this phase untill a certain amount of factories has been bought or all matter is acquired.
            if self.itemCount[Item.Factory] >= 200:
                self.actions.setSlideValue("SwarmSlider", 150)
                self.currentState.goTo(self.states.PlanetaryConsumption)
                self.droneRatio = 2  # Moves drone acquisition to a 1:1 ratio.
                TS.print("Moving to phase PlanetaryConsumption.")

        elif self.currentState.get() == self.states.PlanetaryConsumption:
            # Exhaust planetary matter.
            self.__consumePlanet()

        elif self.currentState.get() == self.states.PrepareThirdPhase:
            # Acquire more Gifts/Yomi before moving to Phase 3.
            self.__prepareThirdPhase()
            if self.info.getInt("Yomi") > 351_158 and self.info.getInt("Processors") >= 110 \
                    and self.info.getInt("Memory") >= 110:
                self.currentState.goTo(self.states.FinishSecondPhase)

        elif self.currentState.get() == self.states.FinishSecondPhase:
            # Acquire resources to buy Space Exploration.
            self.__closeOutSecondPhase()
