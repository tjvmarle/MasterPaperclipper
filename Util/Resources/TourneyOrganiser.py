from Util.Listener import Event, Listener
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
        self.tourneyOn = False
        self.__selectStrat()
        self.start = None

    def __selectStrat(self):
        if self.currStrat == self.stratList[0]:
            return

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
        if self.currStrat == self.stratList[0] and self.start and TS.delta(self.start) < 64:
            # Running a tournament with all strategies takes at least 64s
            return

        if not self.actions.isEnabled("NewTournament"):
            return

        self.__selectStrat()
        self.actions.pressButton("NewTournament")
        self.actions.pressButton("RunTournament")
        self.start = TS.now()

    def tick(self):
        self.__runTourney()
