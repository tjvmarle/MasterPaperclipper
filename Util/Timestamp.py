from typing import List
from datetime import datetime

from selenium.webdriver.common import touch_actions


class Timestamp():
    def __init__(self) -> None:
        pass

    def now() -> datetime:
        return datetime.now()

    def delta(timestamp: datetime) -> float:
        """ Returns the time difference in seconds, including microseconds"""

        tijdsverschil = Timestamp.now() - timestamp
        return float(tijdsverschil.seconds) + float(tijdsverschil.microseconds) / 1000000.0

    def __breakDownTime(timeval: int, unitsize: int, unitname: str, strList: List[str]) -> int:
        """Helper method to break down the timeval into its parts"""

        if timeval < unitsize:
            return timeval

        if strList:
            strList.append(", ")

        count = int(timeval / unitsize)
        timeval -= count * unitsize
        strList.append(f"{count} {unitname}")
        if count > 1:
            strList.append("s")

        return timeval

    def deltaStr(timestamp: datetime) -> str:
        """Gives back a string representation of the elapsed time since timestamp"""

        totalTime = int(Timestamp.delta(timestamp))
        timeString = []
        for secondsPerUnit, unitName in ((60*60*24, "day"), (3600, "hour"), (60, "minute"), (1, "second")):
            totalTime = Timestamp.__breakDownTime(totalTime, secondsPerUnit, unitName, timeString)

        return "".join(timeString)

    def print(text: str) -> None:
        """Print the given text with a timestamp"""

        now = Timestamp.now().strftime("%H:%M:%S")
        print(f"{now}: {text}")
