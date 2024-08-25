import math
from pathlib import Path
import random

from labrea import dataset, Option

from player import Player, PlayerComparison, PlayerScore, Position


_MAGNITUDES = {"1": 1, "2": 2, "3": 4, "4": 8, "5": 16, "6": 32}


@dataset
def players(
        path: str = Option('PATHS.PLAYER', 'players.json'),
        position: Position | None = Option('POSITION', None) >> (lambda p: p if p is None else Position[p]),
        n: float = Option('N', math.inf),
) -> list[Player]:
    all_players = Player.from_json(Path(path).read_text())
    position_players = (p for p in all_players if position is None or p.position is position)
    top_n_players = (p for i, p in enumerate(position_players) if i < n)

    return list(top_n_players)


def _compare_players(p1: Player, p2: Player) -> PlayerComparison:
    prompt = f"""Which player do you prefer?
    1) {p1.name} - {p1.position.name}, {p1.team}
    2) {p2.name} - {p1.position.name}, {p2.team}
    """
    choice: str | None = None
    while choice not in ("1", "2"):
        if choice is not None:
            print("Invalid choice. Please select 1 or 2.")
        choice = input(prompt).strip()

    prompt = f"""How much do you prefer him?
    1) Its a tossup
    2) A little
    3) A tier above
    4) Multiple tiers above
    5) Different leagues
    6) Different galaxies
    """
    difference: str | None = None
    while difference not in _MAGNITUDES:
        if difference is not None:
            print("Invalid choice. Pleas select 1-6.")
        difference = input(prompt).strip()

    return PlayerComparison(p1, p2, (1 if choice == "1" else -1) * _MAGNITUDES[difference])


def rank_player(
        player: Player,
        ranked: list[Player],
) -> tuple[list[Player], list[PlayerComparison]]:
    if len(ranked) == 0:
        return [player], []

    pivot_index = len(ranked) // 2
    better, pivot, worse = ranked[:pivot_index], ranked[pivot_index], ranked[pivot_index+1:]

    comp = _compare_players(player, pivot)

    if comp.difference >= 0:
        better, comps = rank_player(
            player, better,
        )
    else:
        worse, comps = rank_player(
            player, worse,
        )

    return better + [pivot] + worse, [comp] + comps


@dataset
def _ranked_players(players_: list[Player] = players) -> tuple[list[Player], list[PlayerComparison]]:
    ranked: list[Player] = []
    comps: list[PlayerComparison] = []

    for player in random.sample(players_, k=len(players_)):
        ranked, comps = rank_player(player, ranked)

    return ranked, comps


rankings = _ranked_players >> (lambda x: x[0])
comparisons = _ranked_players >> (lambda x: x[1])


@dataset
def scored_players(
        ranks: list[Player] = rankings,
        comps: list[PlayerComparison] = comparisons,
        converge: float = Option('CONVERGENCE_THRESHOLD', 0.001),
        step_rate: float = Option('STEP_RATE', 0.001)
) -> list[PlayerScore]:
    player_scores: dict[Player, float] = {p: 0.0 for p in ranks}

    def _force(c: PlayerComparison) -> float:
        equilibrium = c.difference
        current = player_scores[c.left] - player_scores[c.right]
        return current - equilibrium

    last_loss = math.inf
    loss = 0.0
    while abs(loss-last_loss) > converge:
        for comp in comps:
            force = step_rate * _force(comp)
            player_scores[comp.left] -= force
            player_scores[comp.right] += force

        last_loss, loss = loss, sum(map(_force, comps))

    max_score = max(player_scores.values())
    min_score = min(player_scores.values())

    def _normalize_score(score: float) -> float:
        return 100 * (score - min_score) / (max_score - min_score)

    return sorted(
        (PlayerScore(player, _normalize_score(score)) for player, score in player_scores.items()),
        key=lambda p: -p.score
    )

