# Keeps track of the seperate thread we have running and sets its target
from multiprocessing.dummy import Process
from time import sleep
from Webpage.PageState.PageActions import PageActions, AutoTarget
from Webpage.PageState.PageInfo import PageInfo
from Util.Listener import Event, Listener
from Util.Timestamp import Timestamp as TS
from Util.GameLoop.Phases.CurrentPhase import CurrentPhase, Phase
import re


class ThreadClicker():
    """A semi-independent autoclicker. Main purpose is to maximize the usage of the ~73 clicks we have each second."""
    __enabled = True

    class Disabled():
        """Helper class to temporarily disable the threadclicker. This allows other actions to perform better."""

        def __init__(self) -> None:
            pass

        def __enter__(self) -> None:
            ThreadClicker.__enabled = False

        def __exit__(self, exc_type, exc_value, tb) -> None:
            ThreadClicker.__enabled = True

    def __init__(self, pageInfo: PageInfo, pageAction: PageActions) -> None:
        self.info = pageInfo
        self.actions = pageAction

        self.threadButtons = {AutoTarget.MakePaperclips: "MakePaperclip",
                              AutoTarget.CreateOps: "QuantumCompute",
                              AutoTarget.LaunchProbe: "LaunchProbe"}

        self.photonicActive = False
        self.currentTarget = AutoTarget.MakePaperclips

        # Start the clicker
        self.thread = Process(target=self.__runThreadClicker, args=["1"], name="ThreadClicker")
        self.thread.start()

        Listener.listenTo(Event.BuyProject, self.__activatePhotonics, "Photonic Chip", True)
        Listener.listenTo(Event.ButtonPressed, self.__kill, "IncreaseMaxTrust", True)

    def __runThreadClicker(self, _: str):
        """The main loop of the autoclicker thread."""
        while CurrentPhase.phase != Phase.End:
            if ThreadClicker.__enabled and self.currentTarget != AutoTarget.Off:
                self.actions.threadClick(self.threadButtons[self.currentTarget])
            else:
                sleep(0.1)  # Prevents busywaiting

    def __activatePhotonics(self, _: str) -> None:
        """Callback that allows for checking of the quantum computing values to start."""
        self.photonicActive = True

    def __kill(self, _: str) -> None:
        """Not really a kill, but at least stops the thread more or less for now."""
        ThreadClicker.__enabled = False

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

        self.currentTarget = AutoTarget.CreateOps if total > 0 else altTarget

    def __getPhotonicTotal(self) -> float:
        """Parses the raw HTML to find out if the net quantum value is positive or not. This is a lot faster than 
        checking all the individual fields through self.info."""
        rawHTML = self.info.get("QuantumComputing").get_attribute('innerHTML')
        total = [float(val) for val in re.findall('(?<=opacity: ).+(?=;)', rawHTML)]
        total.pop()  # Opacity of last ops value
        return sum(total)

    def disable() -> None:
        """Deactivates the clicker for a longer time. Temporary solution until I find something cleaner."""
        ThreadClicker.__enabled = False

    def enable() -> None:
        """Re-enables the clicker again."""
        ThreadClicker.__enabled = True
