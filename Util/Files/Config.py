# Class to load in configuration properties and make them globally available
import csv


class Config():
    __config = {}
    __projects = []

    def __init__(self) -> None:
        raise NotImplementedError("We don't do that here.")

    def load(path: str) -> None:
        with open(path) as file:
            lines = file.readlines()

        accumulating = False
        accumulator = []
        for line in lines:
            line = line.strip()

            if line.startswith("#") or not line:
                continue

            if "=[" in line and line.endswith("]"):  # Single line list propery
                keyName, listString = line.replace("[", "").replace("]", "").split("=")
                Config.__config[keyName.strip()] = [listEntry.strip() for listEntry in listString.split(",")]

            elif line.endswith("=["):  # Start of multiline list property
                accumulating = True
                accumulator.append(line.replace("=[", "").strip())

            elif line == "]":  # End of multiline list property
                Config.__config[accumulator[0]] = accumulator[1:]
                accumulating = False
                accumulator.clear()

            elif "=" in line and not accumulating:  # Regular config property
                keyName, value = [entry.strip() for entry in line.split("=")]
                Config.__config[keyName] = value

            else:  # Inside property list
                accumulator.append(line.replace(",", ""))

    def loadProjects(path: str):
        with open(path, "r") as file:
            csvInput = csv.reader(file, delimiter=",")

            projectList = []
            for line in csvInput:
                if not line or line[0].strip().startswith("#"):
                    print(f"Skipped [{line}]")
                    continue

                projectList.append(line)
                print(f"Appended: {projectList[-1]}")

        Config.__config["AllProjects"] = projectList

    def get(param: str) -> str:
        return Config.__config.get(param, "")

    def set(key: str, val) -> None:  # Value may be of any type
        Config.__config[key] = val
