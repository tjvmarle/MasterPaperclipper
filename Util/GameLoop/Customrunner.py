# Seperate runner class for testing purposes.
from selenium import webdriver

from Util.Resources.Progresslogger import Progresslogger
# from Util.GameLoop.Phases.Phase1Step2 import Phase1Step2
from Webpage.PageState.PageActions import PageActions
from Webpage.PageState.PageInfo import PageInfo


class Customrunner():
    def __init__(self, driver: webdriver.Chrome) -> None:
        self.info = PageInfo(driver)
        self.actions = PageActions(driver)
        self.logger = Progresslogger(self.info)

        # Insert custom proc here
        # self.proc = Phase1Step2(self.info, self.actions)

    def tick(self) -> None:
        self.logger.tick()
        self.proc.tick()
