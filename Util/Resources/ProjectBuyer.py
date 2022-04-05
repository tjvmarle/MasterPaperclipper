from functools import partial
from Util.GameLoop.Strategies.CurrentPhase import CurrentPhase, Phase
from Util.Timestamp import Timestamp as TS
from Util.Files.Config import Config
from Util.Listener import Event, Listener
from Webpage.PageState.PageActions import PageActions
from Webpage.PageState.PageInfo import PageInfo
import time


class ProjectBuyer():
    """This class handles acquisition of all projects throughout the entire game."""

    def __init__(self, pageInfo: PageInfo, pageActions: PageActions) -> None:
        self.info = pageInfo
        self.actions = pageActions

        self.highPrioProjects = Config.get("highPriorityProjects")  # Currently only contains phase 1 projects
        self.projects = Config.get("phaseOneProjects")
        self.enoughFunds = False

        Listener.listenTo(Event.ButtonPressed, self.__enoughFundsWithdrawn, "WithdrawFunds", False)
        CurrentPhase.addCbToPhaseMove(Phase.One, self.__setNextProjectList)
        CurrentPhase.addCbToPhaseMove(Phase.Two, self.__setNextProjectList)

    def __enoughFundsWithdrawn(self, _: str) -> None:
        funds = self.info.getFl("Funds")
        self.enoughFunds = (funds > 511_500_000.0)

    def __setNextProjectList(self) -> None:
        if CurrentPhase.phase == Phase.Two:
            self.projects = Config.get("phaseTwoProjects")
        else:
            self.projects = Config.get("phaseThreeProjects")

    def __isBlockActive(self, block: str) -> bool:
        # TODO: These blocks should be controlled from the phases, not from this class
        if block == "block0":
            return not self.enoughFunds

        if block == "block1":
            return (self.info.getInt("Processors") + self.info.getInt("Memory")) < 100

        return False

    def __buyProjects(self):
        # FIXME: Sometimes projects are still being acquired without them being popped of the list.
        boughtProject = []
        photonicChecked = False

        for project in self.highPrioProjects:

            # Optimization
            if project == "Photonic Chip" and photonicChecked or project in self.projects:
                continue

            if self.actions.isEnabled(project):
                if self.actions.pressButton(project):
                    time.sleep(0.5)
                    boughtProject.append(project)
            # Optimization, check only once when a Photonic Chip is disabled
            elif not photonicChecked and project == "Photonic Chip":
                photonicChecked = True

        for project in boughtProject:
            TS.print(f"Bought high prio: {project}.")
            self.highPrioProjects.remove(project)

        if not self.projects:
            for project in boughtProject:
                Listener.notify(Event.BuyProject, project)
            return

        nextProject = self.projects[0]
        blocked = ("block" in nextProject)
        if blocked and not self.__isBlockActive(nextProject):
            blocked = False
            self.projects.pop(0)
            nextProject = self.projects[0]
            TS.print(f"Block1 disabled for ProjectBuyer. Next project is {nextProject}.")

        if not blocked and self.actions.isEnabled(nextProject):
            if self.actions.pressButton(nextProject):
                self.projects.pop(0)
                boughtProject.append(nextProject)
                TS.print(f"Bought {nextProject}.")

                if nextProject == "Another Token of Goodwill":
                    time.sleep(0.25)

        # FIXME: Buying the ninth token seems to fail quite often.
        if self.projects and self.projects[0] == "Another Token of Goodwill" and self.projects.count(
                "Another Token of Goodwill") == 1 and not self.actions.isVisible("Another Token of Goodwill"):
            TS.print("Missed a token of Goodwill, popping it of the list.")
            self.projects.pop(0)

        for project in boughtProject:
            Listener.notify(Event.BuyProject, project)

    def tick(self):
        self.__buyProjects()
