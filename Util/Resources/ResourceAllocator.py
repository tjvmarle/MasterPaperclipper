# Keeps track of available resources and updates accordingly when spending/acquiring
from Util.Resources.CashSpender import CashSpender
from Util.Resources.ProjectBuyer import ProjectBuyer
from Util.Resources.TrustSpender import TrustSpender
from Util.Resources.TourneyOrganiser import TourneyOrganiser
from Webpage.PageState.PageActions import PageActions
from Webpage.PageState.PageInfo import PageInfo


class ResourceAllocator():
    def __init__(self, pageInfo: PageInfo, pageActions: PageActions) -> None:
        self.info = pageInfo
        self.actions = pageActions

        # TODO: design some way to formulate strategies/priorities in spending resources and a way to communicate them with the classes managed here
        self.moneyHandler = CashSpender(self.info, self.actions)
        self.trustee = TrustSpender(self.info, self.actions)
        self.yomi = TourneyOrganiser(self.info, self.actions)
        self.pb = ProjectBuyer(self.info, self.actions)

        self.pb.addProjectNotifier(self.moneyHandler.projectWatcher)
        self.pb.addProjectNotifier(self.moneyHandler.pricer.projectWatcher)

    def tick(self):
        self.moneyHandler.tick()
        self.trustee.tick()
        self.yomi.tick()
        self.pb.tick()
