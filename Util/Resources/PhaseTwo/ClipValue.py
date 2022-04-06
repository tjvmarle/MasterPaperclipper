from selenium.webdriver.remote.webelement import WebElement


class ClipValue():
    """More or less a wrapper for the ingame values. Makes it easier to convert and work with the extremely large 
    values."""

    magnitudes = {"zero": -1, "million": 0, "billion": 1, "trillion": 2, "quadrillion": 3, "quintillion": 4,
                  "sextillion": 5, "septillion": 6, "octillion": 7, "nonillion": 8, "decillion": 9}

    inverse_magnitudes = {}

    def __init__(self, value: WebElement) -> None:
        value = value.text

        if " " not in value:
            number = value
            magnitude = "zero"
        else:
            number, magnitude = value.split(" ")

        self.value = float(number)
        self.magnitude = ClipValue.magnitudes[magnitude]

    def __lt__(self, other) -> bool:
        if self.magnitude == other.magnitude:
            return self.value < other.value
        else:
            return self.magnitude < other.magnitude

    def __eq__(self, other) -> bool:
        return self.value == other.value and self.magnitude == other.magnitude

    def __ne__(self, other) -> bool:
        return not (self == other)

    def __le__(self, other) -> bool:
        return self == other or self < other

    def __mul__(self, factor: float):
        self.value *= factor
        if self.value > 1_000.0 and (self.magnitude + 1) in ClipValue.inverse_magnitudes:
            self.value /= 1_000.0
            self.magnitude += 1

        return self

    def zero(self) -> bool:
        return self.value == 0 and self.magnitude == -1
