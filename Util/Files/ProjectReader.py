from enum import Enum
import csv


# Overview of every resource that could be spent
class Cost(Enum):
    Ops = 1
    Dollars = 2
    Creativity = 3


# Small abstraction for a project
class _Project():
    def __init__(self, name, id, cost) -> None:
        self.name = name
        self.id = id
        self.cost = cost


#  Keeps track of available projects
class ProjectReader():
    def __init__(self) -> None:
        self.projectList = []

    def parseProject(self, name: str, id: str, cost: str) -> None:
        self.projectList.append(_Project(name, id, cost))

    def importProjects(self, path: str) -> None:
        with open(path, "r") as file:
            csvInput = csv.reader(file, delimiter=",")

            for name, id, cost, info in csvInput:
                if name == "Name":
                    continue

                if "Unimportant" in name:
                    # Skip these for now
                    return

                if name:
                    self.parseProject(name, id, cost)
