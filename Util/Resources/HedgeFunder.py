# Responsible for Investments

from Webpage.PageState.PageActions import PageActions
from Webpage.PageState.PageInfo import PageInfo
from Util.Timestamp import Timestamp as TS


class HedgeFunder():
    def __init__(self, pageInfo: PageInfo, pageActions: PageActions) -> None:
        self.investmentsActive = False
        # TODO: Determine at what point you start with investing.
        # Determine minimum investment level and required Yomi
        # Set investment risk
        # Perhaps don't even buy the project until you're ready to invest immediately
        # Find a way to block other funds spending until you're done investing
        pass

    def tick(self):
        # Manage investments
        # Yomi costs for Invest Upgrades: 100 (54), 658 (55), 1981 (56), 4330 (57), 7943 (58), 13038 (59)
        pass

# TODO: Phase 1 ends at 100 trust. We need to buy around 10-20 trust from projects.
# We first need 1 million to buy our competitor.
# After that we need 10 million to buy out all competition.
# Buying 10 trust after that requires 512 million.
# Perhaps buy the revTracker and start with an early, small investment depending on rev/sec
