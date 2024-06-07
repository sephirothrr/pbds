from enum import Enum
from itertools import groupby
import protests


def ordinal(n):
    return "%d%s" % (n, "tsnrhtdd"[(n // 10 % 10 != 1) * (n % 10 < 4) * n % 10::4])


class Status(Enum):
    UNCHECKED = "Status for {1}:{0} has not been checked."
    PENDING = "{} is tentatively in {} place at {}-{} but still has score sheet(s) pending or a tied game pending a protest."
    TWO_WAY_TIEBREAK = "{} and {} are tied for {} place at {}-{} and will need to play a one-stage tiebreaker."
    THREE_WAY_TIEBREAK = "{}, {}, and {} are tied for {} place at {}-{} and will need to play a two-stage tiebreaker."
    FOUR_ACROSS_TWO = "{}, {}, {}, and {} are tied for {} place at {}-{} and will need to play a one-stage tiebreaker."
    FOUR_ACROSS_THREE = "{}, {}, {}, and {} are tied for {} place at {}-{} and will need to play a two-stage tiebreaker."
    COMPLETE = "{} is free to go, in {} place at {}-{}."
    TIED_COMPLETE = "{} is free to go, tied for {} place at {}-{}."
    ERROR = "Something went wrong with {1}:{0}'s status."


# TODO: get real data model from qbj files once they are available

class Team:
    def __init__(self, name: str):
        self.name = name
        self.games = 0
        self.wins = 0
        self.losses = 0
        self.tupoints = 0
        self.tuh = 0
        self.bpoints = 0
        self.position = -1
        self.status = Status.UNCHECKED
        self.color = "white"
        self.protest = False


class Game:
    def __init__(self, rnd: int, tuh: int, team1: str, team1tuscore: int, t1bscore:int, team2: str, team2tuscore: int, t2bscore:int):
        self.round = rnd
        self.tuh = tuh
        self.team1 = team1
        self.team1tuscore = team1tuscore
        self.team1bscore = t1bscore
        self.team1score = team1tuscore + t1bscore
        self.team2 = team2
        self.team2tuscore = team2tuscore
        self.team2bscore = t2bscore
        self.team2score = team2tuscore + t2bscore


class Pool:
    def __init__(self, name: str):
        self.name = name
        self.teams = []
        self._status = []

    @property
    def findStatus(self):
        self.teams.sort(key=lambda x: (x.wins, x.tupoints + x.bpoints), reverse=True)
        breaks = []
        records = []
        for k, g in groupby(self.teams, key=lambda x: (x.wins, x.losses)):
            breaks.append(list(g))
            records.append(k)
        status = []
        rank = 1

        for i, brk in enumerate(breaks):
            block_status = Status.UNCHECKED

            if brk[0].games != 5:
                block_status = Status.PENDING
            else:
                match len(brk):
                    case 1:
                        block_status = Status.COMPLETE
                    case 2:
                        if not rank % 2:
                            block_status = Status.TWO_WAY_TIEBREAK
                        else:
                            block_status = Status.TIED_COMPLETE
                    case 3:
                        block_status = Status.THREE_WAY_TIEBREAK
                    case 4:
                        if rank % 2:
                            block_status = Status.FOUR_ACROSS_TWO
                        else:
                            block_status = Status.FOUR_ACROSS_THREE
                    case _:
                        block_status = Status.ERROR

            for t in range(rank, rank + len(brk)):
                self.teams[t - 1].status = block_status
                self.teams[t - 1].position = rank

            if block_status in (Status.UNCHECKED, Status.ERROR):
                for team in brk:
                    status.append(block_status.value.format(team.name, ordinal(rank)))
            elif block_status in (Status.PENDING, Status.COMPLETE, Status.TIED_COMPLETE):
                for team in brk:
                    status.append(block_status.value.format(team.name, ordinal(rank), records[i][0], records[i][1]))
            else:
                status.append(block_status.value.format(*[t.name for t in brk], ordinal(rank), records[i][0], records[i][1]))

            if block_status in [Status.COMPLETE, Status.TIED_COMPLETE]:
                for team in brk:
                    team.color = "lightgreen"
            elif block_status in [Status.PENDING]:
                for team in brk:
                    team.color = "yellow"
            elif block_status in [Status.TWO_WAY_TIEBREAK, Status.THREE_WAY_TIEBREAK, Status.FOUR_ACROSS_TWO, Status.FOUR_ACROSS_THREE]:
                for team in brk:
                    team.color = "lightcoral"

            rank += len(brk)

        self._status = status
        return status


class Tournament:
    def __init__(self, name: str, pools: list[Pool]):
        self.name = name
        self.pools = pools
