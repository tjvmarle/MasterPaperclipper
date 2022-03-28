# Class to finish out the second phase.

from Util.Resources.ProbeBalancer import ProbeBalancer
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


class PhaseThree():
    def __init__(self, pageInfo: PageInfo, pageActions: PageActions, organiser: TourneyOrganiser) -> None:
        # TODO: Take over the tourneyorganiser + threadclicker from PhaseTwo
        self.info = pageInfo
        self.actions = pageActions

        # TODO: Add a trustspender
        self.tourneyOrganizer = organiser
        self.balancer = ProbeBalancer(self.info, self.actions)
        self.pb = ProjectBuyer(self.info, self.actions)
        self.thread = ThreadClicker(self.info, self.actions)
        self.trustee = TrustSpender(self.info, self.actions)
        self.runners = [self.tourneyOrganizer, self.balancer, self.thread, self.pb, self.trustee]
        self.kill = False

    def checkExploration(self) -> None:
        if "100.00" in self.info.get("SpaceExploration").text:
            self.kill = True

    def tick(self):
        for runner in self.runners:
            runner.tick()

        self.checkExploration()

        if self.kill:
            TS.print(f"End goal reached: converted the universe in {TS.deltaStr(Config.get('Gamestart'))}!")
            ingameTime = self.info.get("Message1").text
            TS.print(f"In-game timer: {ingameTime}")

            self.thread.kill()
            return False

        return True
