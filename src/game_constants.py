from enum import Enum
"""
Stores useful constants about the game
(players should be able to access this in their bot)
"""


class Team(Enum):
    """
    Describes Team State
    """
    RED = 1
    BLUE = 2


class TileState(Enum):
    """
    Describes tile state
    """
    TERRAFORMABLE = 1
    MINING = 2
    IMPASSABLE = 3
    ILLEGAL = 4


class Direction(Enum):
    """
    Describes Robot Movement Directions
    """
    UP = (-1, 0)
    UP_RIGHT = (-1, 1)
    RIGHT = (0, 1)
    DOWN_RIGHT = (1, 1)
    DOWN = (1, 0)
    DOWN_LEFT = (1, -1)
    LEFT = (0, -1)
    UP_LEFT = (-1, -1)


class RobotType(Enum):
    """
    Describes Types of Robots
    """
    MINER = "Miner"
    TERRAFORMER = "Terraformer"
    EXPLORER = "Explorer"


class GameConstants:
    """
    This is an example from last year
    """
    # Map Constants
    MAX_MAP_WIDTH = 48              # max map width
    MAX_MAP_HEIGHT = 48             # max map height
    NUM_TURNS = 200                 # turns per player
    BASE_VISIBLE_RADIUS = 1         # initial visible tiles

    # TIME CONSTANTS
    TIME_LIMIT = 10 + 1 * NUM_TURNS # base time + time per turn

    # Currency Constants
    INIT_BATTERY = 120
    METAL_GAINED_PER_TURN = 10
    INIT_METAL = 200
    MINING_MIN = 5
    MINING_MAX = 25
    TERRAFORM_MAX = 10

    # Robot Action Constants
    EXPLORER_ACTION_COST = 10
    MINER_ACTION_COST = 20
    TERRAFORMER_ACTION_COST = 20
    ROBOT_CHARGE = 30
    ROBOT_SPAWN_COST = 50
    ROBOT_TRANSFORM_COST = 40
