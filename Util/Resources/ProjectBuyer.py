from Util.Timestamp import Timestamp as TS
from Util.AcquisitionHandler import AcquisitionHandler
from Util.Files.Config import Config
from Webpage.PageState.PageActions import PageActions
from Webpage.PageState.PageInfo import PageInfo


class ProjectBuyer():
    def __init__(self, pageInfo: PageInfo, pageActions: PageActions) -> None:
        self.info = pageInfo
        self.actions = pageActions

        self.highPrioProjects = Config.get("highPriorityProjects")
        self.projects = Config.get("phaseOneProjects")
        self.projectNotifiers = []

    def addProjectNotifier(self, handler: AcquisitionHandler) -> None:
        self.projectNotifiers.append(handler)

    def notify(self, project: str):
        for handler in self.projectNotifiers:
            handler.handle(project)

    def __isBlockActive(self, block: str) -> bool:
        if block == "block1":
            return (self.info.getInt("Processors") + self.info.getInt("Memory")) < 100

        return False

    def __buyProjects(self):
        boughtProject = []
        for project in self.highPrioProjects:
            if self.actions.isEnabled(project):
                if self.actions.pressButton(project):
                    boughtProject.append(project)

        for project in boughtProject:
            self.highPrioProjects.remove(project)
            TS.print(f"Bought high prio: {project}.")
            if project in self.projects:
                self.projects.remove(project)

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

            if nextProject in self.highPrioProjects:  # This should rarely occur
                TS.print(f"Race condition encountered, removing {nextProject}.")
                self.highPrioProjects.remove(nextProject)

        for project in boughtProject:
            self.notify(project)

    def tick(self):
        self.__buyProjects()
