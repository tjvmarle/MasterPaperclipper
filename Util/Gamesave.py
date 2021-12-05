from selenium import webdriver
from Util.Timestamp import Timestamp as TS

# Big thanks to Debnath @ https://gist.github.com/debnath for this command!
cmd = r"""var saveGame=localStorage.getItem("saveGame"),savePrestige=localStorage.getItem("savePrestige"),saveProjectsActive=localStorage.getItem("saveProjectsActive"),saveProjectsFlags=localStorage.getItem("saveProjectsFlags"),saveProjectsUses=localStorage.getItem("saveProjectsUses"),saveStratsActive=localStorage.getItem("saveStratsActive"),restoreString="/************* Run the code below to restore your savegame *************/\nlocalStorage.setItem('saveGame', '"+saveGame+"') \nlocalStorage.setItem('savePrestige', '"+savePrestige+"') \nlocalStorage.setItem('saveProjectsActive', '"+saveProjectsActive+"') \nlocalStorage.setItem('saveProjectsFlags', '"+saveProjectsFlags+"') \nlocalStorage.setItem('saveProjectsUses', '"+saveProjectsUses+"') \nlocalStorage.setItem('saveStratsActive', '"+saveStratsActive+"') \n"; return restoreString;"""


# Class to save and load the game
class Gamesave():
    def __init__(self, webdriver: webdriver.Chrome) -> None:
        self.driver = webdriver

    def save(self, path: str) -> None:
        self.driver.execute_script("save()")
        save = self.driver.execute_script(cmd)
        with open(path, "w") as file:
            file.write(save)

        TS.print(f"Progress saved in {path}")

    def load(self, path: str) -> None:
        with open(path, "r") as file:
            file.readline()
            self.driver.execute_script("".join(file.readlines()))
            self.driver.refresh()
