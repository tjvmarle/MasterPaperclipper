# Seperate runner class for testing purposes.
from selenium import webdriver

from Util.GameLoop.Progresslogger import Progresslogger
from Webpage.PageState.PageActions import PageActions
from Webpage.PageState.PageInfo import PageInfo

from Util.Resources.PhotonicClicker import PhotonicClicker


class Customrunner():
    def __init__(self, driver: webdriver.Chrome) -> None:
        self.info = PageInfo(driver)
        self.actions = PageActions(driver)
        self.logger = Progresslogger(self.info, 2)

        # Insert custom proc here
        self.photon = PhotonicClicker(self.info, self.actions)

    def addProc(self, proc) -> None:
        self.photon.append(proc)

    def tick(self) -> bool:
        self.info.tick()
        self.actions.tick()
        self.logger.tick()

        return self.photon.tick()
