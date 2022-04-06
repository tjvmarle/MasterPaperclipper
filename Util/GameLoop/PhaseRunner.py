# Main loop runner. Contains the active running phase and some other functionality.
from selenium import webdriver
from Util.GameLoop.Phases.PhaseOne import PhaseOne
from Util.GameLoop.Phases.CurrentPhase import CurrentPhase, Phase
from Util.Resources.Progresslogger import Progresslogger
from Util.Resources.ThreadClicker import ThreadClicker
from Util.Resources.ProjectBuyer import ProjectBuyer

from Webpage.PageState.PageActions import PageActions
from Webpage.PageState.PageInfo import PageInfo


class PhaseRunner():
    """Main class to handle execution of the three game phases."""

    def __init__(self, driver: webdriver.Chrome) -> None:
        self.info = PageInfo(driver)
        self.actions = PageActions(driver)

        # This one runs outside the game loop.
        self.thread = ThreadClicker(self.info, self.actions)

        self.logger = Progresslogger(self.info)  # Optional, but provides some stats while running the game.
        self.pb = ProjectBuyer(self.info, self.actions)
        self.activePhase = PhaseOne(self.info, self.actions)

        # TODO: Trustspender en TourneyOrganiser can be put here.

        CurrentPhase.addCbToPhaseMove(Phase.One, self.__moveToNextPhase)
        CurrentPhase.addCbToPhaseMove(Phase.Two, self.__moveToNextPhase)

    def tick(self) -> bool:
        self.logger.tick()
        self.thread.tick()
        self.pb.tick()
        self.activePhase.tick()

    def __moveToNextPhase(self):
        self.activePhase = self.activePhase.getNextPhase()
