# Prints overall progress. Mostly used for optimization purposes.
from Util.Files.Config import Config
from Util.Timestamp import Timestamp as TS
from Webpage.PageState.PageInfo import PageInfo
from Webpage.PageState.PageActions import PageActions
from colorama import Fore, Style


class Progresslogger():
    def __init__(self, pageInfo: PageInfo, pageActions: PageActions) -> None:
        self.info = pageInfo
        self.actions = pageActions
        self.interval = int(Config.get("ProgressInterval"))
        self.nrOfIntervals = 1
        self.ticks = 0

    def logProgress(self):
        currVals = [[field, self.info.get(field).text] for field in Config.get("progressFields")]
        currValStrings = [f"{name}={value}" for name, value in currVals if value]
        currValStrings.append(f"fps={(self.ticks / self.interval):.2f}")  # Average fps over interval
        self.ticks = 0

        # UGLY: This needs a more permanent solution. Important performance metric.
        driverAccesCount = self.info.driverAccess
        driverAccesCount += self.actions.driverAccess
        self.info.driverAccess = 0
        self.actions.driverAccess = 0
        driverAccessPerSec = driverAccesCount / self.interval
        currValStrings.append(f"driverAccess/sec={driverAccessPerSec:.2f}")

        TS.print(f"{Fore.LIGHTBLACK_EX}Progress({self.nrOfIntervals}): ",
                 ", ".join(currValStrings), f"{Style.RESET_ALL}")
        # TODO: save values in local file. Perhaps something you can import in a Database or Grafana

    def tick(self):
        self.ticks += 1

        if TS.delta(Config.get("Gamestart")) / self.nrOfIntervals > self.interval:
            self.logProgress()
            self.nrOfIntervals += 1
