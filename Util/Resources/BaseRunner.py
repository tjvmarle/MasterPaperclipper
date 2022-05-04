from typing import Callable, List
from Webpage.PageState.PageActions import PageActions
from Webpage.PageState.PageInfo import PageInfo


class BaseRunner():
    """Base class for the scripts managing aspects of the webpage."""

    def __init__(self, pageInfo: PageInfo, pageActions: PageActions) -> None:
        self.info = pageInfo
        self.actions = pageActions
        self.runners: List[Callable] = []

    def add_runner(self, runner: Callable) -> None:
        """Add a method to be called each tick."""
        self.runners.append(runner)

    def remove_runner(self, runner: Callable) -> None:
        """Remmoves a method from the tick execution."""
        self.runners.remove(runner)

    def tick(self) -> None:
        """Runs all the appended method. Override this method if the tick execution requires additional complexity."""

        for runner in self.runners:
            runner()
