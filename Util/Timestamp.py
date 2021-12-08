from typing import List
from datetime import date, datetime


class Timestamp():
    def __init__(self) -> None:
        """This class is primarly to be used as static"""
        raise NotImplementedError("Class Timestamp is not suppossed to be instantiated.")

    def now() -> datetime:
        """Return current time"""
        return datetime.now()

    def delta(pastTime: datetime, futureTime: datetime = None) -> float:
        """ Returns the time difference in seconds, including microseconds"""

        refTime = futureTime if futureTime else Timestamp.now()
        timeDiff = refTime - pastTime
        return float(timeDiff.seconds) + float(timeDiff.microseconds) / 1000000.0

    def __breakDownTime(timeVal: int, unitSize: int, unitName: str, strList: List[str]) -> int:
        """Helper method to break down the timeval into its parts"""

        if timeVal < unitSize:
            return timeVal

        if strList:
            strList.append(", ")

        count = int(timeVal / unitSize)
        timeVal -= count * unitSize
        strList.append(f"{count} {unitName}")
        if count > 1:
            strList.append("s")

        return timeVal

    def deltaStr(timestamp: datetime) -> str:
        """Gives back a string representation of the elapsed time since timestamp"""

        totalTime = int(Timestamp.delta(timestamp))
        timeString = []
        for secondsPerUnit, unitName in ((60*60*24, "day"), (3600, "hour"), (60, "minute"), (1, "second")):
            totalTime = Timestamp.__breakDownTime(totalTime, secondsPerUnit, unitName, timeString)

        return "".join(timeString)

    def print(*text: str) -> None:
        """Print the given text with a timestamp"""

        now = Timestamp.now().strftime("%H:%M:%S")
        print(f"{now}:", *text)
