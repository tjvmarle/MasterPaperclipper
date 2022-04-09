from Webpage.PageState.PageActions import PageActions
from Webpage.PageState.PageInfo import PageInfo


class SwarmWatcher():
    """Keeps track if the swarm need entertainment or synchronization."""

    def __init__(self, pageInfo: PageInfo, pageActions: PageActions) -> None:
        self.info = pageInfo
        self.actions = pageActions

    def tick(self) -> None:
        if self.actions.isEnabled("EntertainSwarm"):
            self.actions.pressButton("EntertainSwarm")

        if self.actions.isEnabled("SynchronizeSwarm"):
            self.actions.pressButton("SynchronizeSwarm")
