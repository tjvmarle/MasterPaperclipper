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
        self.start = TS.now()

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

                # OPT: trying to fix timing of longest running tournament
                if self.currStrat == self.stratList[0]:
                    self.start = TS.now()
                break

        # Cleanup lower priority strategies
        if self.currStrat != self.stratList[-1]:
            del self.stratList[-1]

    def __runTourney(self):
        if not self.actions.isEnabled("NewTournament"):
            return

        # OPT
        if self.currStrat == self.stratList[0]:
            runTime = TS.delta(self.start)
            TS.print(f"Last Yomi tournament ran for {runTime:.2f} seconds.")
            self.start = TS.now()

        self.__selectStrat()
        self.actions.pressButton("NewTournament")
        self.actions.pressButton("RunTournament")

    def tick(self):
        self.__runTourney()
