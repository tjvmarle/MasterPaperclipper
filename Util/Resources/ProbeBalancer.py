from Webpage.PageState.PageActions import PageActions
from Webpage.PageState.PageInfo import PageInfo


class ProbeBalancer():

    def __init__(self, pageInfo: PageInfo, pageActions: PageActions) -> None:
        # Buy 20 Probe Trust

        self.info = pageInfo
        self.actions = pageActions

        # TODO: check required Yomi for 20 points. Current save doesn't have enough. Stops at 14.
        for _ in range(20):
            self.actions.pressButton("BuyProbeTrust")

        # FIXME: Should be 14 when we have enough Yomi
        for _ in range(8):
            self.actions.pressButton("RaiseReplication")

        for _ in range(6):
            self.actions.pressButton("RaiseHazard")

        # TODO:
        # Create at least some drones, switch Swarm Computing to 99 Think
        # You also need at least a little bit of speed and exploration to gain some matter
        # Monitor gained Yomi, buy additional probe trust

    def tick(self) -> None:
        # If available matter == 0 --> explore a bit
        pass
