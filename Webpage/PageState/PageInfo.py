from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import Select
from Util.Files.Config import Config
from Util.Timestamp import Timestamp as TS


# Class to acquire data from the webpage
class PageInfo():
    """This class handles access to elements for read-only purposes."""

    def __init__(self, webdriver: webdriver.Chrome) -> None:
        self.driver = webdriver

        self.state = {}
        self.text = {}
        self.ids = {name: id for name, id in [listEntry.split(":") for listEntry in Config.get("infoFields")]}

    def update(self, field: str) -> None:
        """Read the value of a data field on the webpage."""
        self.state[field] = self.driver.find_element(By.ID, self.ids[field])

    def get(self, element: str) -> WebElement:
        """Get the contents of a data field. The value will be reused if called for multiple times per tick."""

        # TODO: make this private and cache the calls as a .txt again. Create some error handling if lookup fails.
        if not self.state.get(element, False):
            self.update(element)

        return self.state[element]

    def getInt(self, element: str) -> int:
        """Same as get(), but converts the value to integer."""
        return int(self.get(element).text.replace(",", "").replace(".", ""))

    def getFl(self, element: str) -> float:
        """Same as get(), but converts the value to float."""
        return float(self.get(element).text.replace(",", ""))

    def getAttribute(self, element: str, attribute: str):
        """Retrieves an attribute of a webElement."""
        return self.get(element).get_attribute(attribute)

    def getOptions(self, dropdown: str):
        return [option.text for option in Select(self.get(dropdown)).options if option.text]

    def isVisible(self, element) -> bool:
        return self.get(element).is_displayed()
