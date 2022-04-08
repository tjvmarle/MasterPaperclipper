from Util.GameLoop.Phases.CurrentPhase import CurrentPhase, Phase
from Util.Resources.PhaseThree.ProbeBalancer import ProbeBalancer
from Webpage.PageState.PageActions import PageActions
from Webpage.PageState.PageInfo import PageInfo
from Util.Resources.TourneyOrganiser import TourneyOrganiser
from Util.Timestamp import Timestamp as TS
from Util.Files.Config import Config


class PhaseThree():
    """Class to manage finishing the third phase of the game."""

    def __init__(self, pageInfo: PageInfo, pageActions: PageActions, organiser: TourneyOrganiser, trustSpender) -> None:
        self.info = pageInfo
        self.actions = pageActions

        self.tourneyOrganizer = organiser
        self.balancer = ProbeBalancer(self.info, self.actions)
        self.trustSpender = trustSpender
        self.runners = [self.tourneyOrganizer, self.balancer, self.trustSpender]

    def tick(self) -> None:
        for runner in self.runners:
            runner.tick()

        if "100.00" in self.info.get("SpaceExploration").text:
            TS.print(f"End goal reached: converted the universe in {TS.deltaStr(Config.get('Gamestart'))}!")
            ingameTime = self.info.get("Message1").text
            TS.print(f"In-game timer: {ingameTime}")

            CurrentPhase.moveToNext()
            return False

        return True
