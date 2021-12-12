from Util.Files.Config import Config
from Util.Timestamp import Timestamp as TS
from Webpage.PageState.PageActions import PageActions
from Webpage.PageState.PageInfo import PageInfo


class TourneyOrganiser():
    def __init__(self, pageInfo: PageInfo, pageAction: PageActions) -> None:
        self.info = pageInfo
        self.actions = pageAction
        self.stratList = Config.get("YomiStrategies")[::-1]
        self.currStrat = None
        self.__selectStrat()

    def __selectStrat(self):
        available = self.info.getOptions("PickStrat")
        if not available:
            return

        for bestStrat in self.stratList:
            if bestStrat in available and self.currStrat != bestStrat:
                self.actions.selectFromDropdown("PickStrat", bestStrat)
                self.currStrat = bestStrat
                break

        # Cleanup lower priority strategies
        if self.currStrat != self.stratList[-1]:
            del self.stratList[-1]

    def __runTourney(self):
        if not self.actions.isEnabled("NewTournament"):
            return

        self.__selectStrat()
        self.actions.pressButton("NewTournament")
        self.actions.pressButton("RunTournament")

    def tick(self):
        self.__runTourney()
