from Webpage.PageState.PageActions import PageActions
from Webpage.PageState.PageInfo import PageInfo
from Util.Resources.BaseRunner import BaseRunner
from Util.Resources.State import StateTracker


class StatefulRunner(BaseRunner):
    """Base class for scripts running the webpage that also track an internal state."""

    def __init__(self, pageInfo: PageInfo, pageActions: PageActions, stateClass) -> None:
        """stateClass must be an Enum class"""
        super().__init__(pageInfo, pageActions)

        self.currentState = StateTracker([enum for enum in stateClass])
        self.states = stateClass  # Just a shorthand to refer to the list of internal enum states
