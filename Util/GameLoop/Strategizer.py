# Main module to guide the actions on the webpage. The exact actions are dependent on the current active strategy, which is determined from the current phase and state of the game.
from selenium import webdriver
from Util.GameLoop.Strategies.PhaseOne import PhaseOne
from Util.GameLoop.Progresslogger import Progresslogger
from Webpage.PageState.PageActions import PageActions
from Webpage.PageState.PageInfo import PageInfo


class Strategizer():
    def __init__(self, driver: webdriver.Chrome) -> None:
        self.info = PageInfo(driver)
        self.actions = PageActions(driver)
        self.logger = Progresslogger(self.info, 2)

        # self.phaseRunner = [Phase1Step1(self.info, self.actions)]
        self.phaseRunner = PhaseOne(self.info, self.actions)

    def tick(self) -> bool:
        self.logger.tick()

        return self.phaseRunner.tick()
