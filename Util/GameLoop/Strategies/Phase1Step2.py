# Strategy class for continuing from acquiring Photonic Chips
# Some priorities are: buying projects from free ops, start gathering yomi, get to 100 trust
# Trust buying can be delegated to seperate strategy

from Util.Resources.CashSpender import CashSpender
from Util.Resources.PriceWatcher import PriceWatcher
from Util.Resources.ThreadClicker import ThreadClicker
from Util.Resources.TrustSpender import TrustSpender
from Webpage.PageState.PageActions import PageActions
from Webpage.PageState.PageInfo import PageInfo
from Util.Timestamp import Timestamp as TS
from Util.Files.Config import Config
import time


Alive = True


class Phase1Step2():
    def __init__(self, pageInfo: PageInfo, pageActions: PageActions) -> None:
        self.info = pageInfo
        self.actions = pageActions

        self.projects = Config.get("phaseTwoProjects")

        self.start = Config.get("Gamestart")
        self.thread = ThreadClicker(self.info, self.actions)
        self.fundsHandler = CashSpender(self.info, self.actions)
        self.pricer = PriceWatcher(self.info, self.actions)
        self.trustee = TrustSpender(self.info, self.actions)
        # TODO: yomi tournament organizer
        self.runners = (self.thread, self.fundsHandler, self.pricer, self.trustee)

    def __kill(self):
        """Temporary switch to end the entire session."""
        TS.print("End goal reached!")
        self.thread.kill()
        global Alive
        Alive = False

    def __buyProjects(self):
        if not self.projects:
            return

        projectBttn = self.projects[0]
        if self.actions.isEnabled(projectBttn):
            time.sleep(0.4)  # The buttons 'blink' in
            TS.print(f"Buying {projectBttn}")
            self.actions.pressButton(projectBttn)

            if projectBttn == "Hypno Harmonics":
                # Current kill point
                TS.print(f"Reached {projectBttn} in {TS.deltaStr(self.start)}")
                self.__kill()

            self.projects.pop(0)

    def tick(self):
        self.__buyProjects()

        for runner in self.runners:
            runner.tick()
        return Alive