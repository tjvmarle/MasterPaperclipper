# Basic class for running the gameloop
# TODO:Find out if we're actually going to need this

class LoopRunner():
    def __init__(self) -> None:
        print("LoopRunner created")
        # Perhaps add modules here with tick-actions depending on gamestate?
        self.tickers = []

    def addProcess(self, process):
        """All processes added here require an implementation for tick()"""
        self.tickers.append(process)

    def run(self):
        print("LoopRunner started")
        # TODO: Calculate 'framerate'

        while True:
            for process in self.tickers:

                # Immediately stop the loop if any process returns false
                if not process.tick():
                    return
