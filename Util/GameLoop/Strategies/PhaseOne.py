# Strategy class for continuing from acquiring Photonic Chips
# Some priorities are: buying projects from free ops, start gathering yomi, get to 100 trust
# Trust buying can be delegated to seperate strategy

from Util.AcquisitionHandler import AcquisitionHandler
from Webpage.PageState.PageActions import PageActions
from Webpage.PageState.PageInfo import PageInfo
from Util.Resources.ThreadClicker import ThreadClicker
from Util.Resources.ResourceAllocator import ResourceAllocator
from Util.Timestamp import Timestamp as TS
from Util.Files.Config import Config


class PhaseOne():
    def killPhaseOne(self):
        self.kill = True

    def __init__(self, pageInfo: PageInfo, pageActions: PageActions) -> None:
        self.info = pageInfo
        self.actions = pageActions

        self.resourceManager = ResourceAllocator(self.info, self.actions)
        self.projectWatcher = AcquisitionHandler()
        self.projectWatcher.addHandle("Clip Factories", self.killPhaseOne)
        self.resourceManager.pb.addProjectNotifier(self.projectWatcher)

        self.thread = ThreadClicker(self.info, self.actions)
        self.resourceManager.pb.addProjectNotifier(self.thread.projectWatcher)

        self.runners = (self.thread, self.resourceManager)
        self.kill = False

    def tick(self):
        for runner in self.runners:
            runner.tick()

        # trustKill = 100
        if self.kill:
            # not self.actions.isVisible("Release the HypnoDrones") and self.actions.isVisible("BuyProcessor") and not self.actions.isEnabled("BuyProcessor") and self.info.getInt(
            #         "Processors") + self.info.getInt("Memory") >= trustKill:
            # Current kill point - takes about 48 minutes

            TS.print(f"Phase two reached, startup initialized for global paperclip conversion!")
            self.thread.kill()
            return False

        return True
