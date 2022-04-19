from enum import Enum
from typing import Callable, Tuple, List


class StateTracker():
    """Keeps track of the state within a class to allow for cleaner strategy adaption. Assumes state progression is 
    linear."""

    class _Transition():
        """Helper struct to specify a single state transition."""

        def __init__(self, fromState: Enum, toState: Enum, cb: Callable, transitionOnce: bool) -> None:
            self.fromState = fromState
            self.toState = toState
            self.transitionCallback = cb  # Can either be a trigger to transition or a callback reacting to a one.
            self.transitionOnce = transitionOnce

    def __init__(self, states: Tuple[Enum], startingState: Enum = None) -> None:
        self._states = states
        self._state = states[0] if not startingState else startingState
        self._transitionChecks: List[StateTracker._Transition] = []
        self._transitionTriggers: List[StateTracker._Transition] = []

    def get(self) -> Enum:
        """Retrieves current state."""
        return self._state

    def goTo(self, state: Enum) -> None:
        """Proceeds to given state, triggers any relevant callbacks."""
        prevState = self._state
        self._state = state
        self.__triggerTransition(prevState, self._state)

    def setTransitionCheck(self, fromState: Enum, toState: Enum, callback: Callable, transitionOnce: bool = True) -> None:
        """Set a check to trigger a transition from one state to the next."""
        self._transitionChecks.append(StateTracker._Transition(fromState, toState, callback, transitionOnce))

    def setTransitionTrigger(self, fromState: Enum, toState: Enum, callback: Callable, transitionOnce: bool = True) -> None:
        """Sets a callback to trigger when transitioning from one state to the next."""
        self._transitionTriggers.append(StateTracker._Transition(fromState, toState, callback, transitionOnce))

    def atLeast(self, atLeastState: Enum) -> bool:
        """Checks if the current state is either equal to or after the given state."""
        return self._state == atLeastState or self.after(atLeastState)

    def after(self, afterState: Enum) -> bool:
        """Checks if the current state is after the given state."""
        return self._state > afterState

    def before(self, beforeState: Enum) -> bool:
        """Checks if the current state is before the given state."""
        return not self.after(beforeState) and self._state != beforeState

    def __triggerTransition(self, fromState: Enum, toState: Enum) -> None:
        """Triggers all relevant callbacks when moving from one phase to another one."""
        triggersToRemove: List[StateTracker._Transition] = []

        for trigger in self._transitionTriggers:
            if trigger.fromState == fromState and trigger.toState == toState:
                trigger.transitionCallback()

                if trigger.transitionOnce:
                    triggersToRemove.append(trigger)

        for trigger in triggersToRemove:
            self._transitionChecks.remove(trigger)

    def checkForStateTransitions(self) -> None:
        """Checks if a state change needs to occur."""
        transitionsToRemove: List[StateTracker._Transition] = []
        stateChanges: List[Tuple[(Enum, Enum)]] = []

        for transition in self._transitionChecks:
            if transition.fromState != self._state:
                # Transition entry irrelevant for current state.
                continue

            if transition.transitionCallback():
                self._state = transition.toState
                stateChanges.append((transition.fromState, transition.toState))

                if transition.transitionOnce:
                    transitionsToRemove.append(transition)

        for transition in transitionsToRemove:
            self._transitionChecks.remove(transition)

        for fromState, toState in stateChanges:
            self.__triggerTransition(fromState, toState)
