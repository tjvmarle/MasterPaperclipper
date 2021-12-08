from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import NoSuchElementException
from Util.Files.Config import Config

# Class with all actionable items of the entire page


class PageActions():
    def __get(self, button: str) -> WebElement:
        try:
            page_button = self.driver.find_element(By.ID, self.buttons[button])
        except NoSuchElementException:
            return None
        return page_button

    def __init__(self, webdriver: webdriver.Chrome) -> None:
        self.driver = webdriver
        self.buttons = {  # Combine multiple sources
            **{name: id for name, id in [listEntry.split(":") for listEntry in Config.get("actionFields")]},
            **{name: id for name, id, *_ in Config.get("AllProjects")}}
        self.clipper = self.__get("MakePaperclip")

    def tick(self):
        pass

    def makeClip(self):
        # This doubles performance compared to using pressButton()
        self.clipper.click()

    def pressButton(self, button: str):
        page_button = self.__get(button)
        if page_button and page_button.is_displayed() and page_button.is_enabled():
            page_button.click()

    def isEnabled(self, button) -> bool:
        page_button = self.__get(button)
        return page_button and page_button.is_displayed() and page_button.is_enabled()
