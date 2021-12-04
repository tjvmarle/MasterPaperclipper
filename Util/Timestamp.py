import time
from datetime import datetime


class Timestamp():
    def __init__(self) -> None:
        pass

    def now() -> datetime:
        return datetime.now()

    def delta(timestamp: datetime) -> float:
        """ Returns the time difference in seconds, including microseconds"""

        tijdsverschil = Timestamp.now() - timestamp
        return float(tijdsverschil.seconds) + float(tijdsverschil.microseconds) / 1000000.0

    def deltaStr(timestamp: datetime) -> str:
        totalTime = Timestamp.delta(timestamp)
        timeString = ""
        if totalTime > 3600:
            hours = int(totalTime / 3600)
            totalTime = totalTime - hours * 3600
            timeString += f"{hours} hour"
            if hours > 1:
                timeString += "s"

        if totalTime > 60:
            if timeString:
                timeString += ", "

            minutes = int(totalTime / 60)
            totalTime = totalTime - minutes * 60
            timeString += f"{minutes} minute"

            if minutes > 1:
                timeString += "s"

        if totalTime >= 1:
            if timeString:
                timeString += ", "

            timeString += f"{int(totalTime)} second"

            if totalTime > 1:
                timeString += "s"
        return timeString

    def print(text: str) -> None:
        now = Timestamp.now().strftime("%H:%M:%S")
        print(f"{now}: {text}")
