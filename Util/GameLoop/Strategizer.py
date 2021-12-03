# Main module to guide the actions on the webpage. The exact actions are dependent on the current active strategy, which is determined from the current phase and state of the game.
from enum import Enum

from Util.GameLoop.Strategies.Phase1Step1 import Phase1Step1
from Webpage.PageActions import PageActions
from Webpage.PageInfo import PageInfo

import time


class Phases(Enum):
    Phase1Step1 = 1  # Fresh start of the game
    Phase1Step2 = 2  # Trust becomes available?


class Strategizer():
    def __init__(self, info: PageInfo, actions: PageActions) -> None:
        self.info = info
        self.actions = actions
        self.strats = [Phase1Step1(info, actions)]
        pass

    def tick(self) -> bool:
        self.info.tick()
        self.actions.tick()
        result = True
        for strat in self.strats:
            result = strat.execute()

        return result
