from datetime import datetime, timedelta
import time
from typing import Callable, List, Tuple
from Util.Files.Config import Config
from Util.GameLoop.Phases.CurrentPhase import CurrentPhase, Phase
from Util.Listener import Event, Listener
from Util.Resources.BaseRunner import BaseRunner
from Util.Timestamp import Timestamp as TS
from Webpage.PageState.PageActions import PageActions
from Webpage.PageState.PageInfo import PageInfo
from multiprocessing.dummy import Process


class InfoTracker():
    """Tracks a single infofield during the game's execution. Starts tracking a value when it becomes visible. Stops
    tracking when the field disappears."""

    def __init__(self, pageInfo: PageInfo, field: str, interval: int) -> None:
        self.info = pageInfo
        self.field = field
        self.interval = interval
        self.nrOfMeasurements = -1  # Triggers an immediate measurement when the tracker activates.
        self.data = []
        self.track: Callable = self.__watch

        self.missedTracks = 0

    def __watch(self) -> None:
        """Checks if the required field is actually visible and activates the tracker if it is."""

        if self.info.isVisible(self.field):
            self.startTime = TS.now()
            self.track = self.__track  # Deactivates this watcher and starts the tracker.
        else:
            time.sleep(5)

    def __track(self) -> None:
        """Checks if the tracked field is visible and, if the interval has passed, records it's current value."""

        if TS.delta(self.startTime + timedelta(seconds=self.interval * self.nrOfMeasurements)) < self.interval:
            time.sleep(0.25)  # Lower value increases response time, but also CPU load.
            return

        self.nrOfMeasurements += 1

        if not self.info.isVisible(self.field):
            self.missedTracks += 1

            if self.missedTracks >= 2:  # Two missed tracks in a row kills this tracker.
                del self.data[-1]  # Delete the dummy entry.
                self.track = lambda: time.sleep(5)

            self.data.append((TS.now(), -1))  # Record a dummy value in case it is a fluke.
            return

        self.missedTracks = 0
        self.data.append((TS.now(), self.info.get(self.field).text))

    def run(self) -> None:
        """Main loop for the tracker."""
        while RunReporter.tracking:
            self.track()

    def getName(self) -> str:
        """Returns the trackername. Mostly used to name the relevant thread."""
        return f"{self.field}Tracker"

    def getData(self) -> List[Tuple[datetime, str]]:
        return self.data

    def getField(self) -> str:
        return self.field


class RunReporter(BaseRunner):
    """Collects various statistics during the run and presents a report at the end. Useful for detailed analysis
    afterwards."""
    tracking = True

    def __init__(self, pageInfo: PageInfo, pageActions: PageActions) -> None:
        super().__init__(pageInfo, pageActions)
        self.metrics: List[List[str:str]] = [entry.split(":") for entry in Config.get("ReportingMetrics")]
        self.trackers: List[InfoTracker] = []
        self.phaseDurations: List[str] = []
        self.phaseStart = TS.now()
        self.projectAcquisition: List[Tuple[str, str]] = []
        self.runStart = TS.now()

        self.trackPhaseChanges()
        self.trackProjects()
        self.startTrackers()

    def startTrackers(self) -> None:
        """Tracks all kinds of metrics and reports them after a succesful run."""

        for field, interval in self.metrics:
            # We don't need references to the threads, but we do need them for the tracker objects themselves.
            self.trackers.append(InfoTracker(self.info, field, int(interval)))

        for tracker in self.trackers:
            Process(name=tracker.getName(), target=tracker.run, args=[]).start()  # Fire and forget.

    def writeOut(self) -> None:
        """Writes out all data collected this run."""

        # TODO: Check if we can get this to work from a destructor.
        today = TS.now()
        filename = today.strftime("%Y-%m-%dT%H-%M - RunStats")

        with open(f"Data\\Private\\RunStats\\{filename}.txt", "w") as file:
            file.write(f'Date: {today.strftime("%Y-%m-%d")}\n')
            file.write(f'Start: {today.strftime("%H:%M:%S.%f")[:-5]}\n\n')

            # Write out duration of each phase.
            for line in self.phaseDurations:
                file.write(line + "\n")

            if self.phaseDurations:
                file.write(f"Total duration: {TS.deltaStr(self.runStart)}\n")
                file.write("\n")

            # Write out acquired projects.
            if self.projectAcquisition:
                file.write("Project\n")

            for timestamp, project in self.projectAcquisition:
                file.write(f"{timestamp}, {project}\n")

            # Write out all tracked info-fields.
            for tracker in self.trackers:
                if trackedData := tracker.getData():
                    file.writelines(["\n", tracker.getField(), "\n"])
                else:
                    continue

                for timestamp, datapoint in trackedData:
                    timeString = timestamp.strftime("%Y-%m-%dT%H-%M-%S.%f")[:-5]
                    file.writelines(f"{timeString}, {datapoint}\n")

        RunReporter.tracking = False  # Kills of all threads

    def trackPhaseChanges(self) -> None:
        """Tracks duration of each phase."""
        CurrentPhase.addCbToPhaseMove(Phase.One, self.__phaseChanged)
        CurrentPhase.addCbToPhaseMove(Phase.Two, self.__phaseChanged)
        CurrentPhase.addCbToPhaseMove(Phase.Three, self.__phaseChanged)

    def __phaseChanged(self) -> None:
        """Saves the duration of each phase."""
        if CurrentPhase.phase == Phase.Two:
            self.phaseDurations.append(f"1st Phase duration: {TS.deltaStr(self.phaseStart)}")
        elif CurrentPhase.phase == Phase.Three:
            self.phaseDurations.append(f"2nd Phase duration: {TS.deltaStr(self.phaseStart)}")
        elif CurrentPhase.phase == Phase.End:
            self.phaseDurations.append(f"3rd Phase duration: {TS.deltaStr(self.phaseStart)}")

        self.phaseStart = TS.now()

    def trackProjects(self) -> None:
        """Tracks Acquisition time of every project."""
        Listener.listenTo(Event.BuyProject, self.__appendProject, lambda _: True, False)

    def __appendProject(self, project: str) -> None:
        """Saves the bought project with the timestamp."""
        self.projectAcquisition.append((TS.now().strftime("%Y-%m-%dT%H-%M-%S.%f")[:-5], project))


# TODO: Set up a html file to load/visualize the data. Use some JS to import the results and configure the graphs.
