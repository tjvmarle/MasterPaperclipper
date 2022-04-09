from Util.GameLoop.Phases.CurrentPhase import CurrentPhase, Phase
from Webpage.PageState.PageActions import PageActions
from Webpage.PageState.PageInfo import PageInfo
from Util.Listener import Event, Listener
from Util.Timestamp import Timestamp as TS
from Util.Files.Config import Config


class TrustSpender():
    """Class track and spent the Computational Resources."""

    def __acquiredDonkeySpace(self, _: str):
        self.unBlock = True

    def __acquiredSwarmComputing(self, _: str) -> None:
        self.swarmComputingAcquired = True

    def __init__(self, pageInfo: PageInfo, pageAction: PageActions) -> None:
        self.info = pageInfo
        self.actions = pageAction

        # The order of Processors/Memory acquisition is determined entirely from configuration.
        self.trustStrategies = Config.get("trustSpendingStrategy")

        self.nextStrat = None
        self.unBlock = False
        self.finalStratActive = False
        self.swarmComputingAcquired = False

        # Optimization, tracking internally is (a lot) faster than reading from the page.
        self.Processors = 1
        self.Memory = 1

        Listener.listenTo(Event.BuyProject, self.__acquiredDonkeySpace, "Donkey Space", True)
        Listener.listenTo(Event.BuyProject, self.__acquiredSwarmComputing, "Swarm Computing", True)
        self.__getNextStrat()

    def __getNextStrat(self) -> None:
        """Retrieves the next ratio to work towards. These are loaded initially from the configuration."""

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
        """Check if trust/gifts are available and spend them accordingly."""

        if "block" in self.nextStrat and self.__isBlockActive():
            return

        if CurrentPhase.phase == Phase.One:
            availTrust = self.info.getInt("Trust") - (self.Processors + self.Memory)
        elif self.swarmComputingAcquired:
            availTrust = self.info.getInt("Gifts")
        else:
            return

        while availTrust > 0:
            if self.nextStrat[0] <= self.Processors and self.nextStrat[1] <= self.Memory:
                self.__getNextStrat()

                if "block" in self.nextStrat:
                    return

                continue

            if self.initialDeltaRatio[1] == 0:  # E.g. moving from 20:20 to 40:20
                self.actions.pressButton("BuyProcessor")
                self.Processors += 1
                availTrust -= 1
                continue

            if self.initialDeltaRatio[0] == 0:
                self.actions.pressButton("BuyMemory")
                self.Memory += 1
                availTrust -= 1
                continue

            self.__buyFromRatio()
            availTrust -= 1

    def tick(self) -> None:
        self.__spendTrust()
