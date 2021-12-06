# Class to load in configuration properties and make them globally available

class Config():
    __config = {}

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
                Config.__config[keyName] = [listEntry.strip() for listEntry in listString.split(",")]

            elif line.endswith("=["):  # Start of multiline list property
                accumulating = True
                accumulator.append(line.replace("=[", ""))

            elif line == "]":  # End of multiline list property
                Config.__config[accumulator.pop(0)] = accumulator[:]
                accumulating = False
                accumulator.clear()

            elif "=" in line and not accumulating:  # Regular config property
                keyName, value = [entry.strip() for entry in line.split("=")]
                Config.__config[keyName] = value

            else:  # Inside property list
                accumulator.append(line.replace(",", ""))

    def get(param: str) -> str:
        return Config.__config.get(param, "")
