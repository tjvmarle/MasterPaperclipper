from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import NoSuchElementException
from Util.Files.Config import Config
from Util.Timestamp import Timestamp as TS
from enum import Enum


class AutoTarget(Enum):
    MakePaperclips = 1
    CreateOps = 2
    LaunchProbes = 3

# Class with all actionable items of the entire page


class PageActions():
    def __get(self, button: str) -> WebElement:
        try:
            page_button = self.driver.find_element(By.ID, self.buttons[button])
        except NoSuchElementException:
            return None
        return page_button

    def __initThreadTargets(self):
        for TargetButton, ButtonName in {
                AutoTarget.MakePaperclips: "MakePaperclip", AutoTarget.CreateOps: "QuantumCompute"}.items():
            self.threadButtons[TargetButton] = self.__get(ButtonName)

    def __init__(self, webdriver: webdriver.Chrome) -> None:
        self.driver = webdriver
        self.buttons = {  # Combine multiple sources
            **{name: id for name, id in [listEntry.split(":") for listEntry in Config.get("actionFields")]},
            **{name: id for name, id, *_ in Config.get("AllProjects")}}

        self.paperclip = True
        self.threadButtons = {}
        self.threadTarget = AutoTarget.MakePaperclips
        self.__initThreadTargets()

    def tick(self):
        pass

    def threadClick(self):
        """Seperate function for the threadclicker greatly improves performance over pressButton() 
        Clips: ~80 clips/sec
        Ops: 8-10k over max"""
        self.threadButtons[self.threadTarget].click()

    def setThreadClicker(self, newTarget: AutoTarget) -> None:
        self.threadTarget = newTarget

    def pressButton(self, button: str):
        page_button = self.__get(button)
        if page_button and page_button.is_displayed() and page_button.is_enabled():
            page_button.click()
        else:
            state = "enabled" if page_button.is_displayed() else "visible"
            TS.print(f"Attempted to click {button}, but is was not {state}.")

    def isEnabled(self, button) -> bool:
        page_button = self.__get(button)
        return page_button and page_button.is_displayed() and page_button.is_enabled()
