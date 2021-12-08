# Prints overall progress. Mostly used for optimization purposes.
from Util.Files.Config import Config
from Util.Timestamp import Timestamp as TS
from Webpage.PageState.PageInfo import PageInfo


class Progresslogger():
    def __init__(self, pageInfo: PageInfo, interval: int) -> None:
        self.info = pageInfo
        self.interval = interval * 60
        self.nrOfIntervals = 1

    def logProgress(self):
        currVals = [[field, self.info.get(field)] for field in Config.get("progressFields")]
        currValStrings = [f"{name}={value}" for name, value in currVals if value]

        TS.print(f"Progress({self.nrOfIntervals}): ", ", ".join(currValStrings))
        # TODO: save values in local file

    def tick(self):
        if TS.delta(Config.get("Gamestart")) / self.nrOfIntervals > self.interval:
            self.logProgress()
            self.nrOfIntervals += 1
