# Prints overall progress. Mostly used for optimization purposes.
from Util.Files.Config import Config
from Util.Timestamp import Timestamp as TS
from Webpage.PageState.PageInfo import PageInfo


class Progresslogger():
    def __init__(self, pageInfo: PageInfo) -> None:
        self.info = pageInfo
        self.interval = int(Config.get("ProgressInterval"))
        self.nrOfIntervals = 1
        self.ticks = 0

    def logProgress(self):
        currVals = [[field, self.info.get(field).text] for field in Config.get("progressFields")]
        currValStrings = [f"{name}={value}" for name, value in currVals if value]
        currValStrings.append(f"fps={(self.ticks / self.interval):.2f}")  # Average fps over interval
        self.ticks = 0

        TS.print(f"Progress({self.nrOfIntervals}): ", ", ".join(currValStrings))
        # TODO: save values in local file

    def tick(self):
        self.ticks += 1

        if TS.delta(Config.get("Gamestart")) / self.nrOfIntervals > self.interval:
            self.logProgress()
            self.nrOfIntervals += 1
