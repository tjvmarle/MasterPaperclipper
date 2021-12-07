from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import NoSuchElementException

# Class with all actionable items of the entire page

buttonIds = {"MakePaperclip": "btnMakePaperclip", "LowerPrice": "btnLowerPrice", "RaisePrice": "btnRaisePrice",
             "LevelUpMarketing": "btnExpandMarketing", "BuyWire": "btnBuyWire", "BuyAutoclipper": "btnMakeClipper",
             "BuyMegaClipper": "btnMakeMegaClipper", "BuyProcessor": "btnAddProc", "BuyMemory": "btnAddMem"}

# TODO: Load these from PhaseOneProjects.csv
projectsIds = {
    "Creativity": "projectButton3", "Limerick": "projectButton6", "Lexical Processing": "projectButton13",
    "Combinatory Harmonics": "projectButton14", "The Hadwiger Problem": "projectButton15",
    "The Toth Sausage Conjecture": "projectButton17", "Donkey Space": "projectButton19",
    "New Slogan": "projectButton11", "Catchy Jingle": "projectButton12", "Quantum Computing": "projectButton50",
    "Photonic Chip": "projectButton51"}


class PageActions():
    def __get(self, button: str) -> WebElement:
        try:
            page_button = self.driver.find_element(By.ID, self.buttons[button])
        except NoSuchElementException:
            return None
        return page_button

    def __init__(self, webdriver: webdriver.Chrome) -> None:
        self.driver = webdriver
        self.buttons = {**buttonIds, **projectsIds}
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
