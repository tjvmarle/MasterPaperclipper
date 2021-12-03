# Strategy class for a fresh start of the game.
# Current priorities are: high clip production, buy autoclippers, start trust gathering
# Trust buying can be delegated to seperate strategy
# Making paperclips can be done from a seperate thread

from multiprocessing.dummy import Process
from Webpage.PageActions import PageActions
from Webpage.PageInfo import PageInfo
import time
from Util.Timestamp import Timestamp as TS

MakeClips = True
Alive = True

# TODO: Implement a class to prioritize buying projects. Also load them from a config file.
# Available resources can be determined from page info, but should be balanced against cost of non-project actions
# This is probably going to require some kind of balancer-class then.
# TODO: Implement a class to spend trust. Load the strategy from a file.
# Perhaps we need some kind of allocater class that determines available funds for specific


class Phase1Step1():
    def createPaperclips(self, dummy: str):
        while MakeClips:
            self.actions.makeClip()

    def __init__(self, pageInfo: PageInfo, pageActions: PageActions) -> None:
        self.info = pageInfo
        self.actions = pageActions
        self.highestWireCost = 27
        self.lastPriceAdjustment = TS.now()

        # Temporary, should be replaced by something more long-term
        self.projects = ["Creativity", "Limerick", "Lexical Processing", "Combinatory Harmonics",
                         "The Hadwiger Problem", "The Toth Sausage Conjecture", "Donkey Space"]

        # Immediately start creating paperclips
        p = Process(target=self.createPaperclips, args=["1"])
        p.start()

        for _ in range(22):
            self.actions.pressButton("LowerPrice")

    def __updateWire(self):
        wireCost = int(self.info.get("WireCost"))
        self.highestWireCost = max(wireCost, self.highestWireCost)

        enoughMoney = float(self.info.get("Funds")) > wireCost
        wire = int(self.info.get("Wire").replace(",", ""))

        # Either buy when low or cheap
        if wire < 200 and enoughMoney or wire < 1500 and enoughMoney and wireCost <= 17:
            TS.print("Buy wire")
            self.actions.pressButton("BuyWire")

    def __spendTrust(self):
        if not self.actions.isEnabled("BuyProcessor"):
            return

        trust = int(self.info.get("Trust"))
        procs = int(self.info.get("Processors"))
        mem = int(self.info.get("Memory"))

        # trust, procs, mem = [self.info.get(x) for x in ("Trust", "Processors", "Memory")]

        if procs < 10:
            self.actions.pressButton("BuyProcessor")
        else:
            self.actions.pressButton("BuyMemory")

    def __kill(self):
        # Temporary killswitch
        global MakeClips
        MakeClips = False
        global Alive
        Alive = False

    def __buyProjects(self):
        # Start w/ the creativity costing projects
        if self.projects:
            projectBttn = self.projects[0]
            if self.actions.isEnabled(projectBttn):
                TS.print(f"Buying {projectBttn}")
                time.sleep(0.5)  # The buttons 'blink' in
                self.actions.pressButton(projectBttn)
                self.projects.pop(0)
        else:
            TS.print("End goal reached!")  # End the current run
            time.sleep(3)
            self.__kill()

    def __buyClippers(self):
        autoCost = self.info.get("AutoCost")
        if not autoCost:
            return
        else:
            autoCost = float(autoCost)

        enoughMoney = (float(self.info.get("Funds")) -
                       self.highestWireCost) > autoCost
        if enoughMoney and int(self.info.get("AutoCount")) < 75:
            self.actions.pressButton("BuyAutoclipper")
            self.info.update("Funds")
            # TODO: delegate buying / spending resources to seperate class to keep pageInfo up to date, and also to keep priorities centralized

    def __adjustPrice(self):

        # Only adjust price once every 5 sec.
        if TS.delta(self.lastPriceAdjustment) < 5.0:
            return

        rate, unsold = [int(self.info.get(field).replace(",", ""))
                        for field in ("ClipsPerSec", "Unsold")]

        if rate < 40:
            # Prevents stuttering at low rates
            return

        if unsold > 6 * rate:
            self.actions.pressButton("LowerPrice")
        elif unsold < 3 * rate:
            self.actions.pressButton("RaisePrice")

        self.lastPriceAdjustment = TS.now()

    def execute(self):
        self.__updateWire()
        self.__buyClippers()  # Buying wire is more important than clippers
        self.__adjustPrice()
        self.__spendTrust()
        self.__buyProjects()
        return Alive
