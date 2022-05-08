from Util.GameLoop.Phases.CurrentPhase import CurrentPhase, Phase
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

        self.highPrioProjects = Config.get("phaseOneHighPriorityProjects")
        self.projects = Config.get("phaseOneProjects")
        self.enoughFunds = False
        self.lastAcquisitionTime = TS.now()

        Listener.listenTo(Event.ButtonPressed, self.__enoughFundsWithdrawn, "WithdrawFunds", False)
        CurrentPhase.addCbToPhaseMove(Phase.One, self.__setNextProjectList)
        CurrentPhase.addCbToPhaseMove(Phase.Two, self.__setNextProjectList)

    def __enoughFundsWithdrawn(self, _: str) -> None:
        funds = self.info.getFl("Funds")
        self.enoughFunds = (funds > 511_500_000.0)

    def __setNextProjectList(self) -> None:
        """Loads in the projects for the next phase."""
        if CurrentPhase.phase == Phase.Two:
            self.highPrioProjects = Config.get("phaseTwoHighPriorityProjects")
            self.projects = Config.get("phaseTwoProjects")
        else:
            self.highPrioProjects = Config.get("phaseThreeHighPriorityProjects")
            self.projects = Config.get("phaseThreeProjects")

    def __isBlockActive(self, block: str) -> bool:
        """Checks if a block on project acquisition is still relevant. Sometimes these are required before moving on."""
        # TODO: These blocks should be controlled from the phases, not from this class
        if block == "block0":
            return not self.enoughFunds

        return False

    def __buyProjects(self):
        """Check if any required projects are available and buy them if they are."""

        boughtProjects = []
        photonicChecked = False

        # High prio projects are bought whenever they become available.
        for project in self.highPrioProjects:

            # Optimization
            if project == "Photonic Chip" and photonicChecked or project in self.projects:
                continue

            if self.actions.isEnabled(project):
                if self.actions.pressButton(project):
                    self.lastAcquisitionTime = TS.now()
                    boughtProjects.append(project)

            # Optimization, check only once when a Photonic Chip is disabled
            elif not photonicChecked and project == "Photonic Chip":
                photonicChecked = True

        for project in boughtProjects:
            TS.print(f"Bought high prio: {project}.")
            self.highPrioProjects.remove(project)

        if not self.projects:
            for project in boughtProjects:
                Listener.notify(Event.BuyProject, project)
            return

        # Regular projects are only bought in their specific order.
        nextProject = self.projects[0]
        blocked = ("block" in nextProject)
        if blocked and not self.__isBlockActive(nextProject):
            blocked = False
            self.projects.pop(0)
            nextProject = self.projects[0]
            TS.print(f"Block1 disabled for ProjectBuyer. Next project is {nextProject}.")

        if not blocked and self.actions.isEnabled(nextProject):
            if self.actions.pressButton(nextProject):
                time.sleep(0.2)
                self.lastAcquisitionTime = TS.now()
                self.projects.pop(0)

                if nextProject not in self.projects and self.actions.isVisible(nextProject):
                    TS.print(f"Acquisition of {nextProject} failed, trying again.")
                    self.actions.pressButton(nextProject)
                    time.sleep(0.2)

                if nextProject not in self.projects and nextProject != "Photonic Chip" and self.actions.isVisible(nextProject):
                    TS.print(f"Acquisition of {nextProject} failed again, putting it back on the list.")
                    self.projects.insert(0, nextProject)
                else:
                    boughtProjects.append(nextProject)
                    TS.print(f"Bought {nextProject}.")
                    time.sleep(0.3)

        for project in boughtProjects:
            Listener.notify(Event.BuyProject, project)

    def tick(self) -> None:
        self.__buyProjects()
