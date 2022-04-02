# Strategy class for continuing from acquiring Photonic Chips
# Some priorities are: buying projects from free ops, start gathering yomi, get to 100 trust
# Trust buying can be delegated to seperate strategy

from Webpage.PageState.PageActions import PageActions
from Webpage.PageState.PageInfo import PageInfo
from Util.Listener import Event, Listener
from Util.Resources.ThreadClicker import ThreadClicker
from Util.Resources.ResourceAllocator import ResourceAllocator
from Util.Timestamp import Timestamp as TS
from Util.Files.Config import Config


class PhaseOne():
    def __killPhaseOne(self, _: str):
        self.kill = True

    def __init__(self, pageInfo: PageInfo, pageActions: PageActions) -> None:
        self.info = pageInfo
        self.actions = pageActions

        self.resourceManager = ResourceAllocator(self.info, self.actions)
        Listener.listenTo(Event.BuyProject, self.__killPhaseOne, "Clip Factories", True)
        self.thread = ThreadClicker(self.info, self.actions)
        self.runners = (self.thread, self.resourceManager)
        self.kill = False

    def tick(self):
        for runner in self.runners:
            runner.tick()

        if self.kill:
            TS.print(f"Phase two reached, commence planetary paperclip conversion!")
            return False

        return True
