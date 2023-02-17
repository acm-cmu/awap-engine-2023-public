from src.game_constants import Team
from src.game_state import GameState

class Player:
    """
    Players will write a child class that implements (notably the play_turn method)
    """

    def __init__(self, team: Team):
        self.team = team

    def play_turn(self, game_state: GameState) -> None:
        """
        Play Your Turn
        """
        pass
