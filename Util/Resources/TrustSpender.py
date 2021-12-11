from Webpage.PageState.PageActions import PageActions
from Webpage.PageState.PageInfo import PageInfo
from Util.Files.Config import Config
from Util.Timestamp import Timestamp as TS


class TrustSpender():
    def __init__(self, pageInfo: PageInfo, pageAction: PageActions) -> None:
        self.info = pageInfo
        self.actions = pageAction
        self.trustStrategies = Config.get("trustSpendingStrategy")
        TS.print(f"Initialized trust strategies: {self.trustStrategies}.")
        self.nextStrat = None
        self.__getNextStrat()

    def __getNextStrat(self) -> None:
        if not self.trustStrategies:
            # Pretty much end of phase one. Future kill point.
            TS.print(f"Reached end of Phase One in {TS.deltaStr(self.start)}")
            self.__kill()

        nextEntry = self.trustStrategies.pop(0)  # Either <nr>:<nr> or block<nr>
        self.nextStrat = [int(entry) for entry in nextEntry.split(":")] if ":" in nextEntry else nextEntry

        if "block" in self.nextStrat:
            # Passing this strat requires custom handling somewhere else
            return

        # OPT: Technically you don't need to read the values from the page. Tracking them internally should be faster.
        currProc, currMem = [self.info.getInt(val) for val in ("Processors", "Memory")]
        self.initialDeltaRatio = [self.nextStrat[0] - currProc, self.nextStrat[1] - currMem]

    def __isBlockActive(self) -> bool:
        if self.nextStrat == "block1" and "Donkey Space" not in self.projects:
            self.__getNextStrat()
            return False
        return True

    def __buyFromRatio(self) -> None:
        """ Calculate how far we are from our targetProc/Mem values. Compare this ratio to the initial ratio when we chose our current trustStrategy. If our current ratio is higher (or equal), it means we have a higher delta in Processors than our initial value and are thus behind in acquiring them. Else, we need more Memory. This allows both to progress in a relative way towards their next targets. E.g. going from 10:10 to 12:90 should buy 1 proc, 40 mem, 1 proc, 40 mem."""

        currProc, currMem = [self.info.getInt(val) for val in ("Processors", "Memory")]

        if self.nextStrat[1] - currMem == 0:  # Should probably never occur, but prevents possible division by zero
            self.actions.pressButton("BuyProcessor")

        currDeltaRatio = (self.nextStrat[0] - currProc) / (self.nextStrat[1] - currMem)

        if currDeltaRatio >= self.initialDeltaRatio[0] / self.initialDeltaRatio[1]:
            self.actions.pressButton("BuyProcessor")
        else:
            self.actions.pressButton("BuyMemory")

    def __spendTrust(self):
        while self.actions.isEnabled("BuyProcessor"):
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

    def tick(self):
        self.__spendTrust()
