# Allows to set up triggers among classes for acquiring specific projects


class AcquisitionHandler():
    def __init__(self) -> None:
        self.watchList = {}
        pass

    def addHandle(self, project: str, callback) -> None:
        self.watchList[project] = callback

    def handle(self, project: str) -> None:
        func = self.watchList.get(project, False)
        if func:
            func(project)
