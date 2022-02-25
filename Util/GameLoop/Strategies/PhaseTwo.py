# Class to finish out the second phase.

from Util.Resources.ThreadClicker import ThreadClicker
from Webpage.PageState.PageActions import PageActions
from Webpage.PageState.PageInfo import PageInfo
from Util.Listener import Event, Listener
from Util.Resources.ProjectBuyer import ProjectBuyer
from Util.Resources.TourneyOrganiser import TourneyOrganiser
from Util.Resources.ClipSpender import ClipSpender
from Util.Resources.TrustSpender import TrustSpender
from Util.Timestamp import Timestamp as TS
from Util.Files.Config import Config


class PhaseTwo():
    def __swarmAcquired(self, _: str) -> None:
        self.runners.append(TrustSpender(self.info, self.actions))

    def __killPhaseTwo(self, _: str) -> None:
        self.kill = True

    def __init__(self, pageInfo: PageInfo, pageActions: PageActions, organiser: TourneyOrganiser) -> None:
        self.info = pageInfo
        self.actions = pageActions

        # TODO: Take over the tourneyorganiser + threadclicker from PhaseOne
        self.tourneyOrganizer = organiser
        self.thread = ThreadClicker(self.info, self.actions)
        self.pb = ProjectBuyer(self.info, self.actions)  # Reïnitialize this one for phase two
        self.pm = ClipSpender(self.info, self.actions)
        self.runners = [self.tourneyOrganizer, self.thread, self.pb, self.pm]
        self.kill = False

        Listener.listenTo(Event.BuyProject, self.__swarmAcquired, lambda project: project == "Swarm Computing", True)
        Listener.listenTo(Event.BuyProject, self.__killPhaseTwo, lambda project: project == "Space Exploration", True)

    def tick(self):
        for runner in self.runners:
            runner.tick()

        if self.kill:
            TS.print(f"End goal reached: launched into space in {TS.deltaStr(Config.get('Gamestart'))}!")
            self.thread.kill()
            return False

        return True
