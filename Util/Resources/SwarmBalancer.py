from collections import deque
import time
from Util.GameLoop.Phases.CurrentPhase import CurrentPhase, Phase
from Util.Resources.PhaseTwo.ClipValue import ClipValue
from Util.Resources.StatefulRunner import StatefulRunner
from Util.Resources.OrderedEnum import OrderedEnum
from Util.Timestamp import Timestamp as TS
from Webpage.PageState.PageActions import PageActions
from Webpage.PageState.PageInfo import PageInfo


# TODO: Check if we actually need any state-management. Otherwise change to stateless runner.
class SwarmBalancer(StatefulRunner):
    """Class to keep track of the Swarm Computing setting. Requires its own thread to run."""
    MAX_ADJUSTMENT = 16  # Power of two works best
    MIN_ADJUSTMENT = 1

    class PhaseTwoStates(OrderedEnum):
        """Collection of substates for this class."""
        # TODO: We might not need this one.
        SimpleProductionMatching = 0

    def run(self) -> None:
        """Main loop for this thread."""
        while CurrentPhase.phase != Phase.End and self.active:
            self.__maximizeGifts()
            self.__balance()
            time.sleep(1)  # TODO: Make this dependent on self.prevSlideAdjustments[0], lower value = longer sleep.

    def __init__(self, pageInfo: PageInfo, pageActions: PageActions) -> None:
        super().__init__(pageInfo, pageActions, SwarmBalancer.PhaseTwoStates)
        self.states: SwarmBalancer.PhaseTwoStates

        self.slideVal = 0
        self.prevSlideAdjustments = deque([SwarmBalancer.MAX_ADJUSTMENT]*3, 3)
        self.active = True

        self.__setSlider(90)  # Semi-random starting value

    def __setSlider(self, val: int, override=False) -> None:
        """Set the slider to a specific value. The value is clamped between certain limits."""

        # TODO: Check if should keep pressure more towards Think untill there is enough memory to acquire Drone
        # Flocking: Alignment (100k ops)
        if not override:
            val = max(50, min(199, val))

        if val == self.slideVal:
            return

        self.actions.setSlideValue("SwarmSlider", val)
        self.slideVal = val

    def __maximizeGifts(self) -> None:
        """Ensures the slider is at max value when the swarm timer expires, maximizing acquired gifts."""
        timerText = self.info.get("SwarmTimer").text

        if timerText == "2 seconds" or timerText == "1 second":
            prevVal = self.slideVal
            self.__setSlider(200)
            time.sleep(int(timerText[0]) + 1)
            self.__setSlider(prevVal)

    def __balance(self) -> None:
        """Adjusts the Work/Think-slider when necessary.
            - If we continue in the same direction, repeat previous value.
            --- If we continue three or more times in the same direction, double every next adjustment.
            - If we change direction, halve it. """

        increaseSwarmValue = self.__increaseSwarmCheck()
        if increaseSwarmValue == 0:
            return

        if increaseSwarmValue > 0:
            if self.prevSlideAdjustments[0] > 0:
                adjustment = self.__continueDirection()
            else:
                adjustment = self.__changeDirection()
        else:
            if self.prevSlideAdjustments[0] < 0:
                adjustment = self.__continueDirection()
            else:
                adjustment = self.__changeDirection()

        self.__setSlider(self.slideVal + adjustment)
        self.prevSlideAdjustments.appendleft(int(adjustment))

    def __increaseSwarmCheck(self) -> int:
        """Check if the swarmslider needs an adjustment and in what directions. The type of check performed can change 
        throughout the game."""

        if CurrentPhase.phase == Phase.Two:
            # A small buffer to keep wirePerSec slightly above clipsPerSec. If it's too high you'll end up with too much
            # stock. If it's too low, it will mess up calculations in ClipSpender and hinder factory acquisition.
            productionBuffer = 1.05

            wirePerSec = ClipValue(self.info.get("WirePerSec"))
            clipsPerSec = ClipValue(self.info.get("FactoryClipsPerSec")) * productionBuffer

            if wirePerSec == clipsPerSec:
                return 0

            return 1 if wirePerSec > clipsPerSec else -1
        else:
            # Phase Three
            #TODO: implement
            # Should probably be 200 except when some matter has been explored.
            pass

    def __changeDirection(self) -> int:
        """Gives adjustment value when adjusting in the opposite direction."""
        invertSign = -1 if self.prevSlideAdjustments[0] > 0 else 1
        return invertSign * max(SwarmBalancer.MIN_ADJUSTMENT, abs(self.prevSlideAdjustments[0]) / 2)

    def __continueDirection(self) -> int:
        """Gives adjustment value when continue adjusting in the same direction."""
        if self.prevSlideAdjustments[0] == self.prevSlideAdjustments[1] == self.prevSlideAdjustments[2]:
            # After three consecutive increases, every next adjustment will be doubled.
            sign = self.prevSlideAdjustments[0] / abs(self.prevSlideAdjustments[0])
            return sign * min(SwarmBalancer.MAX_ADJUSTMENT, abs(self.prevSlideAdjustments[0] * 2))
        else:
            return self.prevSlideAdjustments[0]

    def getSlideValue(self) -> int:
        return self.slideVal

    def kill(self) -> None:
        """Kill of the thread."""
        TS.print("Killing the Swarmbakancer.")
        self.active = False
