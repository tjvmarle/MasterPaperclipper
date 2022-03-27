from Webpage.PageState.PageActions import PageActions
from Webpage.PageState.PageInfo import PageInfo
from Util.Listener import Event, Listener
from Util.Timestamp import Timestamp as TS
from Util.Files.Config import Config


class TrustSpender():
    def __hypnoDronesRelease(self, _: str) -> None:
        self.hypnoReleased = True
        pass

    def __acquiredDonkeySpace(self, _: str):
        self.unBlock = True

    def __init__(self, pageInfo: PageInfo, pageAction: PageActions) -> None:
        self.info = pageInfo
        self.actions = pageAction
        self.trustStrategies = Config.get("trustSpendingStrategy")
        self.nextStrat = None
        self.unBlock = False
        self.finalStratActive = False
        self.hypnoReleased = False

        # Optimization, tracking internally is (a lot) faster than reading from the page
        # self.Processors = 1
        # self.Memory = 1

        # Temporary for 2nd phase
        # self.Processors = 40
        # self.Memory = 60

        # Temporary for 3rd phase
        self.Processors = 55
        self.Memory = 115

        Listener.listenTo(Event.BuyProject, self.__acquiredDonkeySpace, lambda project: project == "Donkey Space", True)
        Listener.listenTo(Event.BuyProject, self.__hypnoDronesRelease,
                          lambda project: project == "Release the HypnoDrones", True)
        self.__getNextStrat()

    def __getNextStrat(self) -> None:
        if self.finalStratActive:
            return

        if not self.trustStrategies:
            TS.print(f"Truststrategies exhausted, switching to 10_000:10_000.")
            self.nextStrat = [10_000, 10_000]
            self.finalStratActive = True
            return

        nextEntry = self.trustStrategies.pop(0)  # Either <nr>:<nr> or block<nr>
        self.nextStrat = [int(entry) for entry in nextEntry.split(":")] if ":" in nextEntry else nextEntry

        TS.print(f"Next Trust strategy acquired: {self.nextStrat}.")
        if "block" in self.nextStrat:
            # Passing this strat requires custom handling somewhere else
            return

        self.initialDeltaRatio = [self.nextStrat[0] - self.Processors, self.nextStrat[1] - self.Memory]

    def __isBlockActive(self) -> bool:
        if self.nextStrat == "block1" and self.unBlock:
            self.__getNextStrat()
            return False
        return True

    def __buyFromRatio(self) -> None:
        """ Calculate how far we are from our targetProc/Mem values. Compare this ratio to the initial ratio when we chose our current trustStrategy. If our current ratio is higher (or equal), it means we have a higher delta in Processors than our initial value and are thus behind in acquiring them. Else, we need more Memory. This allows both to progress in a relative way towards their next targets. E.g. going from 10:10 to 12:90 should buy 1 proc, 40 mem, 1 proc, 40 mem."""

        if self.nextStrat[1] - self.Memory == 0:  # Should probably never occur, but prevents possible division by zero
            self.actions.pressButton("BuyProcessor")
            self.Processors += 1
            return

        currDeltaRatio = (self.nextStrat[0] - self.Processors) / (self.nextStrat[1] - self.Memory)

        if currDeltaRatio >= self.initialDeltaRatio[0] / self.initialDeltaRatio[1]:
            self.actions.pressButton("BuyProcessor")
            self.Processors += 1
        else:
            self.actions.pressButton("BuyMemory")
            self.Memory += 1

    def __spendTrust(self):
        if "block" in self.nextStrat and self.__isBlockActive():
            return

        if self.hypnoReleased:
            # Temporary, prevents crashing after reaching 2nd phase.
            return

        # TEMP: for 2nd/3rd phase
        # trust = self.info.getInt("Trust")
        trust = self.info.getInt("Gifts")
        # while trust > self.Processors + self.Memory:
        while trust > 0:
            if self.nextStrat[0] <= self.Processors and self.nextStrat[1] <= self.Memory:
                self.__getNextStrat()
                continue
                if "block" in self.nextStrat:
                    return

            if self.initialDeltaRatio[1] == 0:  # E.g. moving from 20:20 to 40:20
                self.actions.pressButton("BuyProcessor")
                self.Processors += 1
                trust -= 1
                continue

            if self.initialDeltaRatio[0] == 0:
                self.actions.pressButton("BuyMemory")
                self.Memory += 1
                trust -= 1
                continue

            self.__buyFromRatio()
            trust -= 1

    def tick(self):
        self.__spendTrust()
