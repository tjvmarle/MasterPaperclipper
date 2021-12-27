# Class to finish out the second phase.

from Util.Resources.ThreadClicker import ThreadClicker
from Webpage.PageState.PageActions import PageActions
from Webpage.PageState.PageInfo import PageInfo
from Util.Resources.ProjectBuyer import ProjectBuyer
from Util.Resources.TourneyOrganiser import TourneyOrganiser
from Util.Resources.ProductionManager import ProductionManager
from Util.Timestamp import Timestamp as TS
from Util.Files.Config import Config


class PhaseTwo():
    def __init__(self, pageInfo: PageInfo, pageActions: PageActions, organiser: TourneyOrganiser) -> None:
        self.info = pageInfo
        self.actions = pageActions

        # TODO: Take over the tourneyorganiser + threadclicker from PhaseOne
        self.tourneyOrganizer = organiser
        self.thread = ThreadClicker(self.info, self.actions)
        self.pb = ProjectBuyer(self.info, self.actions)  # Reïnitialize this one for phase two
        self.pm = ProductionManager(self.info, self.actions)
        self.runners = [self.tourneyOrganizer, self.thread, self.pb, self.pm]

        # TODO: Add a trustspender after acquiring Swarm Computing

        # Listener.listenTo(Event.BuyProject, self.__killPhaseTwo, lambda project: project == "Clip Factories", True)

    def tick(self):
        for runner in self.runners:
            runner.tick()

        kill = False
        if kill:
            TS.print(f"End goal reached: launched into space in {TS.deltaStr(Config.get('Gamestart'))}!")
            self.thread.kill()
            return False

        return True
