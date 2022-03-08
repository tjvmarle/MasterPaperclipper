from Util.Timestamp import Timestamp as TS
from Util.Files.Config import Config
from Util.Listener import Event, Listener
from Webpage.PageState.PageActions import PageActions
from Webpage.PageState.PageInfo import PageInfo


class ProjectBuyer():
    def __enoughFundsWithdrawn(self, _: str) -> None:
        funds = self.info.getFl("Funds")
        self.enoughFunds = (funds > 511_500_000.0)

    def __init__(self, pageInfo: PageInfo, pageActions: PageActions) -> None:
        self.info = pageInfo
        self.actions = pageActions

        # Phase one stuff
        # self.highPrioProjects = Config.get("highPriorityProjects")
        # self.projects = Config.get("phaseOneProjects")
        # self.projects = Config.get("phaseTwoProjects")

        self.projects = Config.get("phaseThreeProjects")
        self.enoughFunds = False

        Listener.listenTo(Event.ButtonPressed, self.__enoughFundsWithdrawn,
                          lambda button: button == "WithdrawFunds", False)

    def __isBlockActive(self, block: str) -> bool:
        if block == "block0":
            return not self.enoughFunds

        if block == "block1":
            return (self.info.getInt("Processors") + self.info.getInt("Memory")) < 100

        return False

    def __buyProjects(self):
        boughtProject = []
        # photonicChecked = False
        # for project in self.highPrioProjects:

        #     # Optimization
        #     if project == "Photonic Chip" and photonicChecked or project in self.projects:
        #         continue

        #     if self.actions.isEnabled(project):
        #         if self.actions.pressButton(project):
        #             boughtProject.append(project)
        #     # Optimization, check only once when a Photonic Chip is disabled
        #     elif not photonicChecked and project == "Photonic Chip":
        #         photonicChecked = True

        # for project in boughtProject:
        #     TS.print(f"Bought high prio: {project}.")
        #     self.highPrioProjects.remove(project)

        if not self.projects:
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

        for project in boughtProject:
            Listener.notify(Event.BuyProject, project)

    def tick(self):
        self.__buyProjects()
