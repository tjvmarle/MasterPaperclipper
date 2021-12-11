# Keeps track of the seperate thread we have running and sets its target
from multiprocessing.dummy import Process
from Webpage.PageState.PageActions import PageActions, AutoTarget
from Webpage.PageState.PageInfo import PageInfo


class ThreadClicker():
    def createPaperclips(self, dummy: str):
        while self.alive:
            self.actions.threadClick()

    def initThread(self):
        self.thread = Process(target=self.createPaperclips, args=["1"])
        self.thread.start()

    def __init__(self, pageInfo: PageInfo, pageAction: PageActions) -> None:
        self.info = pageInfo
        self.actions = pageAction
        self.alive = True
        self.initThread()

    def kill(self):
        self.alive = False
        self.thread.join()

    def __setThreadButton(self):
        # OPT: This one is probably eating a lot of the performance
        chips = [self.info.getAttribute(f"QuantumChip{i}", "style").replace(";", "").split(":")[1] for i in range(10)]
        total = sum([float(val.strip()) for val in chips])
        self.actions.setThreadClicker(AutoTarget.CreateOps if total > 0 else AutoTarget.MakePaperclips)

    def tick(self) -> bool:
        self.__setThreadButton()
        return True
