from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
from colorama import Fore, Style
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
        page_button = self.cache.get(button, False)
        if page_button:
            return page_button

        try:
            page_button = self.driver.find_element(By.ID, self.buttons[button])
            self.cache[button] = page_button
        except NoSuchElementException:
            return None
        return page_button

    def __initThreadTargets(self) -> None:
        for TargetButton, ButtonName in {
                AutoTarget.MakePaperclips: "MakePaperclip", AutoTarget.CreateOps: "QuantumCompute"}.items():
            self.threadButtons[TargetButton] = self.__get(ButtonName)

    def __init__(self, webdriver: webdriver.Chrome) -> None:
        self.driver = webdriver
        self.buttons = {  # Combine multiple sources
            **{name: id for name, id in [listEntry.split(":") for listEntry in Config.get("actionFields")]},
            **{name: id for name, id, *_ in Config.get("AllProjects")}}

        self.cache = {}
        self.paperclip = True
        self.threadButtons = {}
        self.threadTarget = AutoTarget.MakePaperclips
        self.__initThreadTargets()

    def threadClick(self) -> None:
        """Seperate function for the threadclicker greatly improves performance over pressButton() 
        Clips: ~80 clips/sec
        Ops: 10-25k over max depending on amount of Photonic Chips"""
        self.threadButtons[self.threadTarget].click()

    def setThreadClicker(self, newTarget: AutoTarget) -> None:
        self.threadTarget = newTarget

    def pressButton(self, button: str) -> bool:
        page_button = self.__get(button)
        try:
            page_button.click()
        except StaleElementReferenceException:
            del self.cache[button]
            page_button = self.__get(button)
            page_button.click()
            TS.print(f"Stale reference to {button} encountered while clicking.")
        except Exception as e:
            TS.print(f"Clicking {button} failed with exception {e}.")
            return False
        return True

    def isEnabled(self, button) -> bool:
        page_button = self.__get(button)
        try:
            return page_button and page_button.is_displayed() and page_button.is_enabled()
        except StaleElementReferenceException:
            # Reuse of the same projectbutton for Photonic Chips causes these

            del self.cache[button]
            page_button = self.__get(button)
            return page_button and page_button.is_displayed() and page_button.is_enabled()

    def isVisible(self, button) -> bool:
        page_button = self.__get(button)
        return page_button and page_button.is_displayed()

    def selectFromDropdown(self, dropdown: str, selection: str) -> None:
        Select(self.__get(dropdown)).select_by_visible_text(selection)
