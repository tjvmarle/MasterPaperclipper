# Strategy class for continuing from acquiring Photonic Chips
# Some priorities are: buying projects from free ops, start gathering yomi, get to 100 trust
# Trust buying can be delegated to seperate strategy

from Util.Resources.ThreadClicker import ThreadClicker
from Webpage.PageState.PageActions import PageActions
from Webpage.PageState.PageInfo import PageInfo
from Util.Resources.ResourceAllocator import ResourceAllocator

from Util.Timestamp import Timestamp as TS
from Util.Files.Config import Config
import time


class Phase1Step2():
    def __init__(self, pageInfo: PageInfo, pageActions: PageActions) -> None:
        self.info = pageInfo
        self.actions = pageActions

        self.highPrioProjects = Config.get("highPriorityProjects")
        self.projects = Config.get("phaseTwoProjects")

        self.start = Config.get("Gamestart")
        self.thread = ThreadClicker(self.info, self.actions)
        self.resourceManager = ResourceAllocator(self.info, self.actions)

        self.runners = (self.thread, self.resourceManager)
        self.projectNotifiers = [self.resourceManager.moneyHandler.getCallback()]  # UGLY, but works for now

    def __buyProjects(self):
        boughtProject = []
        for project in self.highPrioProjects:
            if self.actions.isEnabled(project):
                time.sleep(0.5)  # The buttons 'blink' in
                # TODO: get rid of the sleep. Just click and check if you succeed
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
            time.sleep(0.5)  # The buttons 'blink' in
            if self.actions.pressButton(projectBttn):
                self.projects.pop(0)
                boughtProject.append(projectBttn)
                TS.print(f"Bought {projectBttn}.")

            if projectBttn in self.highPrioProjects:  # This should rarely occur
                TS.print(f"Race condition encountered, removing {projectBttn}.")
                self.highPrioProjects.remove(projectBttn)

        for project in boughtProject:
            self.notify(project)

    def addNotifier(self, callback) -> None:
        self.projectNotifiers.append(callback)

    def notify(self, project: str):
        for callback in self.projectNotifiers:
            callback(project)

    def tick(self):
        self.__buyProjects()

        for runner in self.runners:
            runner.tick()

        if self.info.getInt("Trust") >= 100:
            # Current kill point
            TS.print(f"Reached 100 trust in {TS.deltaStr(self.start)}")
            TS.print("End goal reached!")
            self.thread.kill()
            return False

        return True
