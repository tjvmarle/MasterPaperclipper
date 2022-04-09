# Keeps track of the seperate thread we have running and sets its target
from multiprocessing.dummy import Process
from Webpage.PageState.PageActions import PageActions, AutoTarget
from Webpage.PageState.PageInfo import PageInfo
from Util.Listener import Event, Listener
from Util.Timestamp import Timestamp as TS
from Util.GameLoop.Phases.CurrentPhase import CurrentPhase, Phase
import re


class ThreadClicker():
    """A semi-independent autoclicker. Main purpose is to maximize the usage of the ~73 clicks we have each second."""

    def __init__(self, pageInfo: PageInfo, pageAction: PageActions) -> None:
        self.info = pageInfo
        self.actions = pageAction

        self.photonicActive = False
        self.__initThread()

        Listener.listenTo(Event.BuyProject, self.__activatePhotonics, "Photonic Chip", True)

    def __initThread(self) -> None:
        """Starts the autoclicker in a seperate thread."""
        self.thread = Process(target=self.__runThreadClicker, args=["1"], name="ThreadClicker")
        self.thread.start()

    def __runThreadClicker(self, _: str):
        """The main loop of the autoclicker thread."""
        while CurrentPhase.phase != Phase.End:
            self.actions.threadClick()

    def __activatePhotonics(self, _: str) -> None:
        self.photonicActive = True

    def tick(self) -> None:
        """Although the autoclicker runs mostly autonomously, the main loop uses this handle to change it's current 
        target."""
        self.__setThreadButton()

    def __setThreadButton(self) -> None:
        """Determines the target for the autoclicker. This is mostly getting free quantum ops or some phase-dependent 
        alternative target."""

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

    def __getPhotonicTotal(self) -> float:
        """Parses the raw HTML to find out if the net quantum value is positive or not."""
        rawHTML = self.info.get("QuantumComputing").get_attribute('innerHTML')
        total = [float(val) for val in re.findall('(?<=opacity: ).+(?=;)', rawHTML)]
        total.pop()  # Opacity of last ops value
        return sum(total)
