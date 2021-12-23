# Keeps track of the seperate thread we have running and sets its target
from multiprocessing.dummy import Process
from Webpage.PageState.PageActions import PageActions, AutoTarget
from Webpage.PageState.PageInfo import PageInfo
from Util.Listener import Event, Listener
from Util.Timestamp import Timestamp as TS


class ThreadClicker():
    def nextPhase(self, _: str) -> None:
        self.phaseOne = False

    def activatePhotonics(self, _: str) -> None:
        self.photonicActive = True

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
        self.photonicActive = False
        self.initThread()
        self.photonicChips = [self.info.get(f"QuantumChip{i}") for i in range(10)]
        Listener.listenTo(Event.BuyProject, self.activatePhotonics, lambda project: project == "Photonic Chip", True)
        Listener.listenTo(Event.BuyProject, self.nextPhase, lambda project: project == "MegaClippers", True)
        self.phaseOne = True

    def kill(self):
        self.alive = False
        self.thread.join()

    def __setThreadButton(self):
        # TODO: ignore making paperclips @ high Clips/second. Almost no benefit
        altTarget = AutoTarget.MakePaperclips if self.phaseOne else AutoTarget.Off
        total = -1
        if self.photonicActive:
            chips = [element.get_attribute("style").replace(";", "").split(":")[1]
                     for element in self.photonicChips]
            total = sum([float(val.strip()) for val in chips])
        self.actions.setThreadClicker(AutoTarget.CreateOps if total > 0 else altTarget)

    def tick(self) -> bool:
        self.__setThreadButton()
        return True
