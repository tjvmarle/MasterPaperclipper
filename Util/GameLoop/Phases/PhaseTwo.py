from Util.GameLoop.Phases.PhaseThree import PhaseThree
from Webpage.PageState.PageActions import PageActions
from Webpage.PageState.PageInfo import PageInfo
from Util.GameLoop.Phases.CurrentPhase import CurrentPhase
from Util.Listener import Event, Listener
from Util.Resources.TourneyOrganiser import TourneyOrganiser
from Util.Resources.PhaseTwo.ClipSpender import ClipSpender
from Util.Resources.TrustSpender import TrustSpender


class PhaseTwo():
    """Class to manage finishing the second phase of the game."""

    def __swarmAcquired(self, _: str) -> None:
        self.runners.append(self.trustSpender)

    def __init__(self, pageInfo: PageInfo, pageActions: PageActions, organiser: TourneyOrganiser,
                 trustSpender: TrustSpender) -> None:
        self.info = pageInfo
        self.actions = pageActions

        self.tourneyOrganizer = organiser
        self.trustSpender = trustSpender
        self.clipsSpender = ClipSpender(self.info, self.actions)

        self.runners = [self.tourneyOrganizer, self.clipsSpender]

        Listener.listenTo(Event.BuyProject, self.__swarmAcquired, "Swarm Computing", True)

        # The trigger to end this phase and move to the next
        # OPT: Spend a few minutes increasing processors, memory, creativity and yomi before finishing out the phase
        # 351.658 yomi is required to buy 20 probe trust in phase three
        # It would also help to have at least 175k creativity to buy Strategic Attachment
        Listener.listenTo(Event.BuyProject, CurrentPhase.moveToNext, "Space Exploration", True)

    def tick(self) -> None:
        for runner in self.runners:
            runner.tick()

    def getNextPhase(self):
        return PhaseThree(self.info, self.actions, self.tourneyOrganizer, self.trustSpender)
