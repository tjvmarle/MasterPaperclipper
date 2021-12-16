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

        projectBttn = self.projects[0]
        if self.actions.isEnabled(projectBttn):
            if self.actions.pressButton(projectBttn):
                self.projects.pop(0)
                boughtProject.append(projectBttn)
                TS.print(f"Bought {projectBttn}.")

            if projectBttn in self.highPrioProjects:  # This should rarely occur
                TS.print(f"Race condition encountered, removing {projectBttn}.")
                self.highPrioProjects.remove(projectBttn)

        for project in boughtProject:
            self.notify(project)

    def tick(self):
        self.__buyProjects()
