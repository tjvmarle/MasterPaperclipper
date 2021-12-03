from selenium import webdriver
from selenium.webdriver.common.by import By

# Class with the state of the entire page

# Should be possible to read exact current state from the page. This would allow to resume from saves, as all other modules should be state-dependent in their actions anyway
# TODO: This does require exact mapping of the states though --> 3 main states and several substates.
# This would also mean other modules would require pretty much nothing to read the current page.
# Tracking/determing the state could be done in seperate class.

# TODO: Perhaps dump this in an external config file
pageIds = {"TotalClips": "clips", "Funds": "funds", "Unsold": "unsoldClips", "ClipPrice": "margin", "Demand": "demand", "MarketingLevel": "marketingLvl", "MarketingCost": "adCost", "ClipsPerSec": "clipmakerRate", "Wire": "wire",
           "WireCost": "wireCost", "AutoCount": "clipmakerLevel2", "AutoCost": "clipperCost", "MegaCount": "megaClipperLevel", "MegaCost": "megaClipperCost", "Trust": "trust", "Processors": "processors", "Memory": "memory", "Creativity": "creativity"}

# TODO: Perhaps map de Ids to specific types and return values converted to those types


class PageInfo():
    def __init__(self, webdriver: webdriver.Chrome) -> None:
        self.driver = webdriver
        self.state = {}
        self.update()

    def update(self, field=None):
        if not field:
            for webId in pageIds:
                self.state[webId] = self.driver.find_element(
                    By.ID, pageIds[webId]).text
        else:
            self.state[field] = self.driver.find_element(
                By.ID, pageIds[field]).text

    def get(self, attribute) -> str:
        return self.state[attribute]

    def tick(self):
        self.update()
