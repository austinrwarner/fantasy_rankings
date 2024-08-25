from dataclasses import dataclass
from enum import Enum
import json


class Position(Enum):
    RB = 'RB'
    WR = 'WR'
    TE = 'TE'
    QB = 'QB'


@dataclass
class Player[T: Position]:
    name: str
    team: str
    position: T

    def update(self, **kwargs) -> "Player":
        return Player(
            **{
                'name': self.name,
                'team': self.team,
                'position': self.position,
                **kwargs
            }
        )

    @classmethod
    def from_dict(cls, __d: dict[str, str]) -> "Player":
        if 'position' in __d:
            __d = {**__d, 'position': Position[__d['position']]}

        return cls(**__d)

    @classmethod
    def from_json(cls, __x: str) -> list["Player"]:
        j: list[dict[str, str]] = json.loads(__x)
        if isinstance(j, dict):
            j = [j]

        return [cls.from_dict(d) for d in j]

    def __hash__(self):
        return hash((self.name, self.team, self.position))


@dataclass
class PlayerComparison:
    left: Player
    right: Player
    difference: float

    def __hash__(self):
        return hash((self.left, self.right, self.difference))


@dataclass
class PlayerScore:
    player: Player
    score: float = 0.0

    def __hash__(self):
        return hash((self.player, self.score))
