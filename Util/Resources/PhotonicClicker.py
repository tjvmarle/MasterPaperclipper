# Keeps track of the quantum states and optimizes production of ops
from multiprocessing.dummy import Process
import time
from Webpage.PageState.PageActions import PageActions, AutoTarget
from Webpage.PageState.PageInfo import PageInfo
from Util.Timestamp import Timestamp as TS


Alive = True


class PhotonicClicker():

    # TODO: centralize this thing somewhere
    # Temporary, thread should already be running
    def createPaperclips(self, dummy: str):
        while Alive:
            self.actions.threadClick()

    def initThread(self):
        p = Process(target=self.createPaperclips, args=["1"])
        p.start()

    def __init__(self, pageInfo: PageInfo, pageAction: PageActions) -> None:
        self.info = pageInfo
        self.actions = pageAction
        self.started = False

    def __determineQuantum(self):
        """Find out where we exactly are in the quantum cycle"""
        pass

    def __setThreadButton(self):
        # Switch the threadclicker to QuantumButton button if it is > 0
        _, val = self.info.getAttribute("QuantumChip0", "style").replace(";", "").split(":")
        self.actions.setThreadClicker(AutoTarget.CreateOps if float(val.strip()) > 0 else AutoTarget.MakePaperclips)

    def tick(self) -> bool:
        if not self.started:
            self.initThread()
            self.started = True

        self.__setThreadButton()
        return True
