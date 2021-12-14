# Strategy class for continuing from acquiring Photonic Chips
# Some priorities are: buying projects from free ops, start gathering yomi, get to 100 trust
# Trust buying can be delegated to seperate strategy

from Webpage.PageState.PageActions import PageActions
from Webpage.PageState.PageInfo import PageInfo
from Util.Resources.ThreadClicker import ThreadClicker
from Util.Resources.ResourceAllocator import ResourceAllocator
from Util.Timestamp import Timestamp as TS
from Util.Files.Config import Config
import time


class Phase1Step2():
    def __init__(self, pageInfo: PageInfo, pageActions: PageActions) -> None:
        self.info = pageInfo
        self.actions = pageActions

        self.thread = ThreadClicker(self.info, self.actions)
        self.resourceManager = ResourceAllocator(self.info, self.actions)

        self.runners = (self.thread, self.resourceManager)

    def tick(self):
        for runner in self.runners:
            runner.tick()

        trustKill = 100
        if self.info.getInt("Trust") >= trustKill:
            # Current kill point
            TS.print(f"Reached {trustKill} trust in {TS.deltaStr(Config.get('Gamestart'))}")
            TS.print("End goal reached!")
            self.thread.kill()
            return False

        return True
