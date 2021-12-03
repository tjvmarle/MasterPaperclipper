import time
from datetime import datetime


class Timestamp():
    def __init__(self) -> None:
        pass

    def now() -> datetime:
        return datetime.now()

    def delta(timestamp: datetime) -> float:
        tijdsverschil = Timestamp.now() - timestamp
        return float(tijdsverschil.seconds) + float(tijdsverschil.microseconds) / 1000000.0
