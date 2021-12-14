# Keeps track of the seperate thread we have running and sets its target
from multiprocessing.dummy import Process
from Webpage.PageState.PageActions import PageActions, AutoTarget
from Webpage.PageState.PageInfo import PageInfo


class ThreadClicker():
    def runThreadClicker(self, dummy: str):
        while self.alive:
            self.actions.threadClick()

    def initThread(self):
        self.thread = Process(target=self.runThreadClicker, args=["1"])
        self.thread.start()

    def __init__(self, pageInfo: PageInfo, pageAction: PageActions) -> None:
        self.info = pageInfo
        self.actions = pageAction
        self.alive = True
        self.initThread()
        self.photonicChips = [self.info.get(f"QuantumChip{i}") for i in range(10)]

    def kill(self):
        self.alive = False
        self.thread.join()

    def __setThreadButton(self):
        # TODO: ignore making paperclips @ high Clips/second. Almost no benefit
        chips = [element.get_attribute("style").replace(";", "").split(":")[1] for element in self.photonicChips]
        total = sum([float(val.strip()) for val in chips])
        self.actions.setThreadClicker(AutoTarget.CreateOps if total > 0 else AutoTarget.MakePaperclips)

    def tick(self) -> bool:
        self.__setThreadButton()
        return True
