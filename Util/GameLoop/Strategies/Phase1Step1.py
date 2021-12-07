# Strategy class for a fresh start of the game.
# Current priorities are: high clip production, buy autoclippers, start trust gathering
# Trust buying can be delegated to seperate strategy
# Making paperclips can be done from a seperate thread

from multiprocessing.dummy import Process
from Webpage.PageState.PageActions import PageActions
from Webpage.PageState.PageInfo import PageInfo
import time
from Util.Timestamp import Timestamp as TS
from Util.Files.Config import Config

Alive = True


class Phase1Step1():
    def createPaperclips(self, dummy: str):
        while Alive:
            self.actions.makeClip()

    def __getNextStrat(self) -> None:
        if not self.trustStrategies:
            # Pretty much end of phase one. Future kill point.
            TS.print(f"Reached end of Phase One in {TS.deltaStr(self.start)}")
            self.__kill()

        nextEntry = self.trustStrategies.pop(0)  # Either <nr>:<nr> or block<nr>
        self.nextStrat = [int(entry) for entry in nextEntry.split(":")] if ":" in nextEntry else nextEntry
        TS.print(f"Next trustStrategy acquired: {self.nextStrat}")

        if "block" in self.nextStrat:
            return

        # OPT: Technically you don't need to read the values from the page. Tracking them internally should be faster.
        currProc, currMem = [self.info.getInt(val) for val in ("Processors", "Memory")]
        self.initialDeltaRatio = [self.nextStrat[0] - currProc, self.nextStrat[1] - currMem]

    def __init__(self, pageInfo: PageInfo, pageActions: PageActions) -> None:
        self.info = pageInfo
        self.actions = pageActions

        self.projects = Config.get("phaseOneProjects")
        self.trustStrategies = Config.get("trustSpendingStrategy")
        self.nextStrat = None

        self.highestWireCost = 27
        self.lastPriceAdjustment = TS.now()
        self.start = TS.now()  # TODO: acquire from Config.

        # Immediately start creating paperclips
        p = Process(target=self.createPaperclips, args=["1"])
        p.start()

        for _ in range(22):
            self.actions.pressButton("LowerPrice")

    def __updateWire(self):
        wireCost = self.info.getInt("WireCost")
        self.highestWireCost = max(wireCost, self.highestWireCost)

        if self.info.getFl("Funds") < wireCost:
            return

        wire = self.info.getInt("Wire")
        # Either buy when low or cheap
        if wire < 200 or (wire < 1500 and wireCost <= 17):
            self.actions.pressButton("BuyWire")

    def __isBlockActive(self) -> bool:
        if self.nextStrat == "block1" and "Donkey Space" not in self.projects and self.info.getInt("Creativity") > 70:
            self.__getNextStrat()
            return False
        return True

    def __buyFromRatio(self) -> None:
        """ Calculate how far we are from our targetProc/Mem values. Compare this ratio from the initial ratio when we chose our current trustStrategy. If our current ratio is higher (or equal), it means we have a higher delta in Processors than our initial value and are thus behind in acquiring them. Else, we need more Memory. This allows both to progress in a relative way towards their next targets. E.g. going from 10:10 to 12:90 should buy 1 proc, 40 mem, 1 proc, 40 mem."""

        currProc, currMem = [self.info.getInt(val) for val in ("Processors", "Memory")]

        if self.nextStrat[1] - currMem == 0:  # Should probably never occur, but prevents possible division by zero
            self.actions.pressButton("BuyProcessor")

        currDeltaRatio = (self.nextStrat[0] - currProc) / (self.nextStrat[1] - currMem)

        if currDeltaRatio >= self.initialDeltaRatio[0] / self.initialDeltaRatio[1]:
            self.actions.pressButton("BuyProcessor")
        else:
            self.actions.pressButton("BuyMemory")

    # TODO: Managing trust/resources should probably be in its own class
    def __spendTrust(self):

        while self.actions.isEnabled("BuyProcessor"):
            if not self.nextStrat:  # Initialization
                self.__getNextStrat()

            if self.nextStrat == [self.info.getInt(var) for var in ("Processors", "Memory")]:
                self.__getNextStrat()

            if "block" in self.nextStrat and self.__isBlockActive():
                return

            if self.initialDeltaRatio[1] == 0:  # E.g. moving from 20:20 to 40:20
                self.actions.pressButton("BuyProcessor")
                continue

            if self.initialDeltaRatio[0] == 0:
                self.actions.pressButton("BuyMemory")
                continue

            self.__buyFromRatio()

    def __kill(self):
        # Temporary killswitch
        TS.print("End goal reached!")
        global Alive
        Alive = False

    def __buyProjects(self):
        if self.projects:
            projectBttn = self.projects[0]
            if self.actions.isEnabled(projectBttn):
                TS.print(f"Buying {projectBttn}")
                time.sleep(0.5)  # The buttons 'blink' in
                self.actions.pressButton(projectBttn)

                if projectBttn == "Photonic Chip":
                    # Current kill point, takes about 16 minutes for now.
                    TS.print(f"Reached Photonic Chips in {TS.deltaStr(self.start)}")
                    self.__kill()

                self.projects.pop(0)

    def __buyClippers(self):
        autoCost = self.info.get("AutoCost")
        if not autoCost:
            return
        else:
            autoCost = float(autoCost)

        enoughMoney = (self.info.getFl("Funds") - self.highestWireCost) > autoCost
        if enoughMoney and self.info.getInt("AutoCount") < 75:
            self.actions.pressButton("BuyAutoclipper")
            self.info.update("Funds")
            # TODO: delegate buying / spending resources to seperate class to keep pageInfo up to date, and also to keep priorities centralized

    def __adjustPrice(self):
        # Only adjust price once every x sec.
        # TODO: Improve balancing. Still has an issue to swing a bit too much.
        # OPT: Optimize to lose a bit less money on the lower side, this slows down buying early clippers
        if TS.delta(self.lastPriceAdjustment) < 7.5:
            return

        rate, unsold = [self.info.getInt(field) for field in ("ClipsPerSec", "Unsold")]

        if rate < 40:
            # Prevents stuttering at low rates
            return

        if unsold > 6 * rate:
            self.actions.pressButton("LowerPrice")
        elif unsold < 3 * rate:
            self.actions.pressButton("RaisePrice")

        self.lastPriceAdjustment = TS.now()

    # TODO: Perhaps buy Marketing a couple of times.
    def execute(self):
        self.__updateWire()
        self.__buyClippers()  # Buying wire is more important than clippers
        self.__adjustPrice()
        self.__spendTrust()
        self.__buyProjects()
        return Alive
