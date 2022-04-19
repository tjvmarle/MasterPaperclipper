from pickle import NONE
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
import time
import sys

sys.tracebacklimit = 0


class AutoTarget(Enum):
    Off = 0
    MakePaperclips = 1
    CreateOps = 2
    LaunchProbe = 3

# Class with all actionable items of the entire page


class PageActions():
    """This class handles access to elements for actionable purposes."""

    def __init__(self, webdriver: webdriver.Chrome) -> None:
        self.driver = webdriver
        self.buttons = {  # Combine multiple sources
            **{name: id for name, id in [listEntry.split(":") for listEntry in Config.get("actionFields")]},
            **{name: id for name, id, *_ in Config.get("AllProjects")}}

        self.cache = {}
        self.paperclip = True

    def __get(self, button: str) -> WebElement:
        """Translates an interactable element to its webelement. Keeps a cache of retrieved elements to increase 
        performance."""
        page_button = self.cache.get(button, False)
        if page_button:
            return page_button

        try:
            # These calls take about 13-14 ms each and take up over 99.9% of the script's execution time.
            page_button = self.driver.find_element(By.ID, self.buttons[button])
            self.cache[button] = page_button
        except NoSuchElementException:
            return None
        return page_button

    def threadClick(self, targetButton: str) -> None:
        """Seperate function for the threadclicker greatly improves performance over pressButton() 
        Clips: ~75 clips/sec
        Ops: 10-35k over max depending on amount of Photonic Chips."""
        try:
            self.__get(targetButton).click()
        except:
            # Not a problem as long as it isn's excessive
            TS.print(f"Threadclick failed on target {targetButton}.")

    def pressButton(self, button: str) -> bool:
        """Tries to click on a button. Will attempt a second time if the reference has gone stale. Assumes the button is 
        clickable."""
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
                TS.print(f"Second attempt at clicking [{button}] failed again.")
                return False

        except Exception as e:
            exc_txt = str(e)
            msg = exc_txt.split('\n')[0]
            TS.print(f"Clicking [{button}] failed with exception [{msg}].")
            return False

        return True

    def isVisible(self, button) -> bool:
        """Checks if an interactable element is visible on the webpage."""
        page_button = self.__get(button)
        try:
            return page_button and page_button.is_displayed()

        except StaleElementReferenceException:
            del self.cache[button]

            page_button = self.__get(button)
            if page_button:
                return page_button.is_displayed()
            else:
                # FIXME: This seems to trigger all the time.
                # TS.print(f"Could not retrieve [{button}], executing isVisible() failed.")
                return False

        except Exception as e:
            TS.print(f"Performing isVisible() on [{button}] failed with exception [{e}].")
            return False
        # page_button = self.__get(button)
        # return page_button and self.__trySafe(button, page_button.is_displayed)

    def isEnabled(self, button: str) -> bool:
        """Checks if an interactable element is enabled on the webpage. Will also check if it is visible first."""
        page_button = self.__get(button)
        try:
            return page_button and self.isVisible(button) and page_button.is_enabled()

        except StaleElementReferenceException:
            del self.cache[button]

            page_button = self.__get(button)
            if page_button:
                return self.isVisible(button) and page_button.is_enabled()
            else:
                TS.print(f"Could not retrieve {button}, executing isEnabled() failed.")
                return False
        except Exception as e:
            TS.print(f"Performing isEnabled() on {button} failed with exception {e}.")
            return False

    def selectFromDropdown(self, dropdown: str, selection: str) -> None:
        """Selects an option from a dropdown list."""
        Select(self.__get(dropdown)).select_by_visible_text(selection)

    def setSlideValue(self, sliderName: str, value: int) -> None:
        """Sets a slider to a specified value. This is done directly in javascript on the webpage instead of using the
        Selenium, because this isn't supported."""
        slider = self.buttons.get(sliderName, False)
        if not slider:
            return

        self.driver.execute_script(f'document.getElementById("{slider}").value = {value}')
