# Seperate runner class for testing purposes.
from selenium import webdriver

from Util.GameLoop.Progresslogger import Progresslogger
from Util.GameLoop.Strategies.Phase1Step2 import Phase1Step2
from Webpage.PageState.PageActions import PageActions
from Webpage.PageState.PageInfo import PageInfo
from Util.Files.Config import Config


class Customrunner():
    def __init__(self, driver: webdriver.Chrome) -> None:
        self.info = PageInfo(driver)
        self.actions = PageActions(driver)
        self.logger = Progresslogger(self.info, self.actions)

        # Insert custom proc here
        self.proc = Phase1Step2(self.info, self.actions)

    def addProc(self, proc) -> None:
        self.proc.append(proc)

    def tick(self) -> bool:
        self.info.tick()
        self.logger.tick()

        return self.proc.tick()
