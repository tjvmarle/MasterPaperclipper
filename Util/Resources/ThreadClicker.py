# Keeps track of the seperate thread we have running and sets its target
from multiprocessing.dummy import Process
from Webpage.PageState.PageActions import PageActions, AutoTarget
from Webpage.PageState.PageInfo import PageInfo
from Util.Listener import Event, Listener
from Util.Timestamp import Timestamp as TS
from Util.GameLoop.Phases.CurrentPhase import CurrentPhase, Phase
import re


class ThreadClicker():
    def __nextPhase(self, _: str) -> None:
        TS.print(f"Killing off autoclicker for making paperclips.")
        self.phaseOne = False

    def __activatePhotonics(self, _: str) -> None:
        self.photonicActive = True

    def __runThreadClicker(self, _: str):
        while self.alive:
            self.actions.threadClick()

    def __initThread(self):
        self.thread = Process(target=self.__runThreadClicker, args=["1"])
        self.thread.start()

    def __getPhotonicTotal(self) -> float:
        # Parsing the raw HTML is a lot faster.
        rawHTML = self.info.get("QuantumComputing").get_attribute('innerHTML')
        total = [float(val) for val in re.findall('(?<=opacity: ).+(?=;)', rawHTML)]
        total.pop()  # Opacity of last ops value
        return sum(total)

    def __init__(self, pageInfo: PageInfo, pageAction: PageActions) -> None:
        self.info = pageInfo
        self.actions = pageAction
        self.alive = True
        self.photonicActive = False
        self.__initThread()
        self.phaseOne = True

        # Dis- and enabled for phase two
        Listener.listenTo(Event.BuyProject, self.__activatePhotonics, lambda project: project == "Photonic Chip", True)
        Listener.listenTo(Event.BuyProject, self.__nextPhase, lambda project: project == "MegaClippers", True)

    def __setThreadButton(self):
        if CurrentPhase.phase == Phase.One:
            altTarget = AutoTarget.MakePaperclips

        elif CurrentPhase.phase == Phase.Two:
            altTarget = AutoTarget.Off

        else:
            altTarget = AutoTarget.LaunchProbe

        total = -1
        if self.photonicActive:
            total = self.__getPhotonicTotal()
        self.actions.setThreadClicker(AutoTarget.CreateOps if total > 0 else altTarget)

    def tick(self) -> None:
        self.__setThreadButton()
        return True
