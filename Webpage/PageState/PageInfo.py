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
        self.state[field] = self.driver.find_element(By.ID, self.ids[field]).text

    def get(self, attribute: str) -> str:
        """Get the contents of a data field. The value will be reused if called for multiple times per tick."""
        if not self.state.get(attribute, False):  # Lazy lookup
            self.update(attribute)

        return self.state[attribute]

    def getInt(self, attribute: str) -> int:
        """Same as get(), but converts the value to integer."""
        return int(self.get(attribute).replace(",", "").replace(".", ""))

    def getFl(self, attribute: str) -> float:
        """Same as get(), but converts the value to float."""
        return float(self.get(attribute))

    def tick(self) -> None:
        """Deprecates all data."""
        self.state = {}
