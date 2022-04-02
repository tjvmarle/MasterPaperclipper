# Main loop runner. Contains the active running phase and some other functionality.
from selenium import webdriver
from Util.GameLoop.Strategies.PhaseOne import PhaseOne
from Util.GameLoop.Strategies.PhaseTwo import PhaseTwo
from Util.GameLoop.Strategies.PhaseThree import PhaseThree
from Util.GameLoop.Strategies.CurrentPhase import CurrentPhase, Phase
from Util.GameLoop.Progresslogger import Progresslogger
from Util.Resources.TourneyOrganiser import TourneyOrganiser
from Webpage.PageState.PageActions import PageActions
from Webpage.PageState.PageInfo import PageInfo
from Util.Timestamp import Timestamp as TS


class Strategizer():
    def __init__(self, driver: webdriver.Chrome) -> None:
        self.info = PageInfo(driver)
        self.actions = PageActions(driver)

        self.logger = Progresslogger(self.info)

        self.phase = Phase.First
        self.runningPhase = PhaseOne(self.info, self.actions)  # Finishes after 45-60 min.
        # self.currentPhase = PhaseTwo(self.info, self.actions, TourneyOrganiser(
        #     self.info, self.actions))  # Takes about 20-30 min
        # self.currentPhase = PhaseThree(self.info, self.actions, TourneyOrganiser(self.info, self.actions))

    def tick(self) -> bool:
        self.logger.tick()

        if self.runningPhase.tick():
            return True
        else:
            return self.moveToNextPhase()

    def moveToNextPhase(self):
        # TODO: Also transfer/fix the threadclicker.
        # TODO: Also transfer/fix the projectbuyer.
        if self.phase == CurrentPhase:
            organizer = self.runningPhase.resourceManager.tourneyOrganizer  # Ugly as hell, we'll fix it later
            self.runningPhase = PhaseTwo(self.info, self.actions, organizer)
        elif self.phase == 2:
            organizer = self.runningPhase.tourneyOrganizer
            self.runningPhase = PhaseThree(self.info, self.actions, organizer)
        else:
            TS.print("Congratulations!")  # Finished the game?
            return False

        self.phase += 1
        return True
