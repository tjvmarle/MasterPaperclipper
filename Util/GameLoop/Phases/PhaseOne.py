# Strategy class for continuing from acquiring Photonic Chips
# Some priorities are: buying projects from free ops, start gathering yomi, get to 100 trust
# Trust buying can be delegated to seperate strategy

from Util.GameLoop.Phases.CurrentPhase import CurrentPhase, Phase
from Webpage.PageState.PageActions import PageActions
from Webpage.PageState.PageInfo import PageInfo
from Util.Listener import Event, Listener
from Util.Resources.PhaseOne.ResourceAllocator import ResourceAllocator
from Util.GameLoop.Phases.PhaseTwo import PhaseTwo
import time


class PhaseOne():
    """Class to manage finishing the first phase of the game."""

    def __init__(self, pageInfo: PageInfo, pageActions: PageActions) -> None:
        """Finishing the first phase takes about 45-60 min."""
        self.info = pageInfo
        self.actions = pageActions

        self.resourceManager = ResourceAllocator(self.info, self.actions)
        self.runners = (self.resourceManager,)

        # The trigger to end this phase and move to the next
        Listener.listenTo(Event.BuyProject, CurrentPhase.moveToNext, "Release the HypnoDrones", True)
        CurrentPhase.addCbToPhaseMove(Phase.One, lambda: time.sleep(4))  # The transition takes a few seconds.

    def tick(self) -> None:
        for runner in self.runners:
            runner.tick()

    def getNextPhase(self):
        return PhaseTwo(self.info, self.actions, self.resourceManager.tourneyOrganizer, self.resourceManager.trustSpender)
