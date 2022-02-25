from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
from colorama import Fore, Style
from Util.Listener import Event, Listener
from Util.Timestamp import Timestamp as TS
from Util.Files.Config import Config
from enum import Enum


class AutoTarget(Enum):
    Off = 0
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

    def __unCachePhotonic(self, _: str):
        # Small optimization
        # FIXME: didn't work. Still stale references when buying these.
        del self.cache["Photonic Chip"]

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

        Listener.listenTo(Event.BuyProject, self.__unCachePhotonic, lambda project: project == "Photonic Chip", False)

    def threadClick(self) -> None:
        """Seperate function for the threadclicker greatly improves performance over pressButton() 
        Clips: ~75 clips/sec
        Ops: 10-35k over max depending on amount of Photonic Chips"""
        if self.threadTarget == AutoTarget.Off:
            return

        try:
            self.threadButtons[self.threadTarget].click()
        except:
            # Not a problem as long as it isn's excessive
            TS.print(f"Threadclick failed on target {self.threadTarget}.")

    def setThreadClicker(self, newTarget: AutoTarget) -> None:
        self.threadTarget = newTarget

    def pressButton(self, button: str) -> bool:
        page_button = self.__get(button)
        try:
            if not page_button:
                return False

            page_button.click()
            Listener.notify(Event.ButtonPressed, button)
        except StaleElementReferenceException:  # Reuse of 'Another Token of Goodwill' causes these
            del self.cache[button]

            page_button = self.__get(button)
            if page_button:
                page_button.click()
                Listener.notify(Event.ButtonPressed, button)
            else:
                TS.print(f"Second attempt at clicking {button} failed again.")
                return False
        except Exception as e:
            TS.print(f"Clicking {button} failed with exception {e}.")
            return False
        return True

    def isVisible(self, button) -> bool:
        page_button = self.__get(button)
        try:
            return page_button and page_button.is_displayed()
        except StaleElementReferenceException:
            del self.cache[button]

            page_button = self.__get(button)
            if page_button:
                TS.print(f"Stale reference encountered to {button}, attempting a second time.")
                return page_button.is_displayed()
            else:
                TS.print(f"Could not retrieve {button}, executing isVisible() failed.")
                return False
        except Exception as e:
            TS.print(f"Performing isVisible() on {button} failed with exception {e}.")
            return False
        # page_button = self.__get(button)
        # return page_button and self.__trySafe(button, page_button.is_displayed)

    def isEnabled(self, button: str) -> bool:
        page_button = self.__get(button)
        try:
            return page_button and self.isVisible(button) and page_button.is_enabled()
        except StaleElementReferenceException:
            del self.cache[button]

            page_button = self.__get(button)
            if page_button:
                TS.print(f"Stale reference encountered to {button}, attempting a second time.")
                return self.isVisible(button) and page_button.is_enabled()
            else:
                TS.print(f"Could not retrieve {button}, executing isEnabled() failed.")
                return False
        except Exception as e:
            TS.print(f"Performing isEnabled() on {button} failed with exception {e}.")
            return False

    def selectFromDropdown(self, dropdown: str, selection: str) -> None:
        Select(self.__get(dropdown)).select_by_visible_text(selection)

    def setSlideValue(self, sliderName: str, value: int) -> None:
        slider = self.buttons.get(sliderName, False)
        if not slider:
            return

        # Using direct js, because Selenium support for these is absent
        self.driver.execute_script(f'document.getElementById("{slider}").value = {value}')
