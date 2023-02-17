from src.game_constants import Team, TileState, GameConstants, RobotType, Direction
from dataclasses import dataclass

@dataclass
class RobotInfo:
    """
    RobotInfo object contains all information about a robot
    """
    battery: int
    acted: bool
    moved: bool
    action_cost: int
    row: int
    col: int
    team: Team
    name: str
    type: RobotType


@dataclass
class TileInfo:
    """
    TileInfo object contains all information about a tile
    """
    state: TileState
    row: int
    col: int
    terraform: int
    mining: int
    robot: RobotInfo

@dataclass
class GameInfo:
    """
    GameInfo object contains all information about the game state
    """
    ally_robots: dict[str, RobotInfo]
    enemy_robots: dict[str, RobotInfo]
    map: list[list[str]]
    metal: int
    team: Team
    robot_spawn_cost: int
    robot_transform_cost: int
    time_left: float
    turn: int