# Keeps track of available resources and updates accordingly when spending/acquiring
from Util.Listener import Event, Listener
from Util.Resources.CashSpender import CashSpender
from Util.Resources.ProjectBuyer import ProjectBuyer
from Util.Resources.TrustSpender import TrustSpender
from Util.Resources.TourneyOrganiser import TourneyOrganiser
from Webpage.PageState.PageActions import PageActions
from Webpage.PageState.PageInfo import PageInfo

from Util.Timestamp import Timestamp as TS


class ResourceAllocator():
    def __addTournament(self, _: str):
        self.tourneyOrganizer = TourneyOrganiser(self.info, self.actions)
        self.runners.append(self.tourneyOrganizer)

    def __trustActivator(self):
        if not self.trustActivated and self.info.isVisible("Trust"):
            ts = TrustSpender(self.info, self.actions)
            self.runners.append(ts)
            self.trustActivated = True

    def __init__(self, pageInfo: PageInfo, pageActions: PageActions) -> None:
        self.info = pageInfo
        self.actions = pageActions
        self.trustActivated = False
        self.moneyHandler = CashSpender(self.info, self.actions)
        self.runners = [self.moneyHandler]

        Listener.listenTo(Event.BuyProject, self.__addTournament, lambda project: project == "Strategic Modeling", True)

    def tick(self):
        self.__trustActivator()

        for runner in self.runners:
            runner.tick()
