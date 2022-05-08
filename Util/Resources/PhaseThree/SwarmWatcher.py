from Webpage.PageState.PageActions import PageActions
from Webpage.PageState.PageInfo import PageInfo
from Util.Timestamp import Timestamp as TS


class SwarmWatcher():
    """Keeps track if the swarm need entertainment or synchronization."""

    def __init__(self, pageInfo: PageInfo, pageActions: PageActions) -> None:
        self.info = pageInfo
        self.actions = pageActions

    def tick(self) -> None:
        if self.actions.isEnabled("EntertainSwarm"):
            TS.print("Entertaining the Swarm.")
            self.actions.pressButton("EntertainSwarm")

        if self.actions.isEnabled("SynchronizeSwarm"):
            TS.print("Synchronizing the Swarm.")
            self.actions.pressButton("SynchronizeSwarm")
