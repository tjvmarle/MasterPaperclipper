from selenium import webdriver
from selenium.webdriver.common.by import By
from Util.Files.Config import Config


# Class to acquire data from the webpage
class PageInfo():
    def __init__(self, webdriver: webdriver.Chrome) -> None:
        self.driver = webdriver

        self.state = {}
        self.ids = {name: id for name, id in [listEntry.split(":") for listEntry in Config.get("infoFields")]}

    def update(self, field: str) -> None:
        """Read the value of a data field on the webpage."""
        self.state[field] = self.driver.find_element(By.ID, self.ids[field])  # .text

    def get(self, element: str):
        """Get the contents of a data field. The value will be reused if called for multiple times per tick."""
        if not self.state.get(element, False):  # Lazy lookup
            self.update(element)

        return self.state[element]

    def getInt(self, element: str) -> int:
        """Same as get(), but converts the value to integer."""
        return int(self.get(element).text.replace(",", "").replace(".", ""))

    def getFl(self, element: str) -> float:
        """Same as get(), but converts the value to float."""
        return float(self.get(element).text)

    def getAttribute(self, element: str, attribute: str):
        """Same as get(), but converts the style to float."""
        return self.get(element).get_attribute(attribute)

    def tick(self) -> None:
        """Deprecates all data."""
        self.state = {}
