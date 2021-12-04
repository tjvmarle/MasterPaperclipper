from selenium import webdriver
from selenium.webdriver.common.by import By

# Class with the state of the entire page

# Should be possible to read exact current state from the page. This would allow to resume from saves, as all other modules should be state-dependent in their actions anyway
# TODO: This does require exact mapping of the states though --> 3 main states and several substates.
# This would also mean other modules would require pretty much nothing to read the current page.
# Tracking/determing the state could be done in seperate class.

# TODO: Perhaps dump this in an external config file
pageIds = {
    "TotalClips": "clips", "Funds": "funds", "Unsold": "unsoldClips", "ClipPrice": "margin", "Demand": "demand",
    "MarketingLevel": "marketingLvl", "MarketingCost": "adCost", "ClipsPerSec": "clipmakerRate", "Wire": "wire",
    "WireCost": "wireCost", "AutoCount": "clipmakerLevel2", "AutoCost": "clipperCost", "MegaCount": "megaClipperLevel",
    "MegaCost": "megaClipperCost", "Trust": "trust", "Processors": "processors", "Memory": "memory",
    "Creativity": "creativity"}


class PageInfo():
    def __init__(self, webdriver: webdriver.Chrome) -> None:
        self.driver = webdriver

        # TODO: These dicts could be fused into one
        self.state = {}
        self.stateCurrent = {}

    def update(self, field) -> None:
        self.state[field] = self.driver.find_element(By.ID, pageIds[field]).text
        self.stateCurrent[field] = True

    def get(self, attribute) -> str:
        if attribute not in self.stateCurrent or not self.stateCurrent[attribute]:
            self.update(attribute)

        return self.state[attribute]

    def getInt(self, attribute) -> int:
        return int(self.get(attribute).replace(",", "").replace(".", ""))

    def getFl(self, attribute) -> float:
        return float(self.get(attribute))

    def tick(self) -> None:
        # Mark all data as deprecated
        self.stateCurrent = dict.fromkeys(self.stateCurrent, False)
