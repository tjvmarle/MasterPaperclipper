# Keeps track of available resources and updates accordingly when spending/acquiring
from Util.Resources.CashSpender import CashSpender
from Util.Resources.ProjectBuyer import ProjectBuyer
from Util.Resources.TrustSpender import TrustSpender
from Util.Resources.TourneyOrganiser import TourneyOrganiser
from Util.AcquisitionHandler import AcquisitionHandler
from Webpage.PageState.PageActions import PageActions
from Webpage.PageState.PageInfo import PageInfo


class ResourceAllocator():
    def addTournament(self, _: str):
        # TODO: TO should have an AcHandler for Theory of Mind -->
        self.runners.append(TourneyOrganiser(self.info, self.actions))

    def trustActivator(self):
        if not self.trustActivated and self.info.isVisible("Trust"):
            ts = TrustSpender(self.info, self.actions)
            self.runners.append(ts)
            self.pb.addProjectNotifier(ts.projectWatcher)
            self.trustActivated = True

    def __init__(self, pageInfo: PageInfo, pageActions: PageActions) -> None:
        self.info = pageInfo
        self.actions = pageActions
        self.trustActivated = False
        self.moneyHandler = CashSpender(self.info, self.actions)
        self.pb = ProjectBuyer(self.info, self.actions)
        self.runners = [self.moneyHandler, self.pb]

        self.projectWatcher = AcquisitionHandler()
        self.projectWatcher.addHandle("Strategic Modeling", self.addTournament)

        # TODO: Clean up this mess. Just make an object or callback to add these.
        self.pb.addProjectNotifier(self.projectWatcher)
        self.pb.addProjectNotifier(self.moneyHandler.projectWatcher)
        self.pb.addProjectNotifier(self.moneyHandler.pricer.projectWatcher)

    def tick(self):
        self.trustActivator()

        for runner in self.runners:
            runner.tick()
