from dataclasses import dataclass
from src.robot import Robot
from src.game_constants import RobotType, Team
import json
import pathlib


@dataclass
class Turn:
    team: str
    turn_number: int
    metal: int
    num_robots: int
    time_left: float
    tiles_explored: list[tuple[int, int]]
    tiles_terraformed: list[tuple[int, int]]
    robot_changes: list[tuple[str, int, int, str, int]]

@dataclass
class ReplayMetadata:
    game_name: str
    map_name: str
    map_height: int
    map_width: int
    red_bot: str
    blue_bot: str
    initial_metal: int
    winner: str


class Replay:
    def __init__(
        self,
        game_name: str,
        map_name: str,
        map_height: int,
        map_width: int,
        red_bot: str,
        blue_bot: str,
        initial_metal: int,
        initial_map_passability: list[tuple[int, int]],
        initial_map_metal: list[tuple[int, int, int]],
        initial_map_terraformed: list[tuple[int, int, int]],
        initial_map_visible: list[tuple[int, int, int]],
    ):
        self.metadata = ReplayMetadata(
            game_name,
            map_name,
            map_height,
            map_width,
            red_bot,
            blue_bot,
            initial_metal,
            None
        )

        self.initial_map_passability = initial_map_passability
        self.initial_map_metal = initial_map_metal
        self.initial_map_terraformed = initial_map_terraformed
        self.initial_map_visible = initial_map_visible
        self.turns: list[Turn] = []
        self.explored_tiles = []
        self.terraformed_tiles = []
        self.robot_changes = []

    def add_explored_tiles(self, tiles: list[tuple[int, int]]) -> None:
        self.explored_tiles.extend(tiles)

    def add_terraformed_tiles(self, tiles: list[tuple[int, int]]) -> None:
        self.terraformed_tiles.extend(tiles)

    def add_robot_changes(self, robot: Robot, terminate: bool) -> None:
        # Add Robot to Replay File and return
        entry = []
        entry.append(robot.get_name())
        # Add Co-ordinates
        if terminate:
            entry.append(-1)
            entry.append(-1)
        else:
            entry.append(robot.get_coord()[0])
            entry.append(robot.get_coord()[1])
        # Add Type
        if (robot.get_type() == RobotType.EXPLORER):
            entry.append("e")
        elif (robot.get_type() == RobotType.MINER):
            entry.append("m")
        else:
            entry.append("t")
        # Add Battery
        entry.append(robot.get_battery())
        # Add Robot Team
        if(robot.get_team() == Team.RED):
            entry.append("red")
        else:
            entry.append("blue")
        self.robot_changes.append(tuple(entry))

    def addTurn(self, team: str, time_left : float, num_robots : int, turn_number: int, metal: int, timeout = False):
        # If timeout, than add turn while ignoring tiles
        if timeout:
            turn = Turn(
                team,
                turn_number,
                metal,
                num_robots,
                time_left,
                [],
                [],
                []
            )
            self.turns.append(turn)
            return
        # Add Turn
        turn = Turn(
            team,
            turn_number,
            metal,
            num_robots,
            time_left,
            self.explored_tiles,
            self.terraformed_tiles,
            self.robot_changes
        )
        self.turns.append(turn)
        # Empty Lists
        self.explored_tiles = []
        self.terraformed_tiles = []
        self.robot_changes = []

    def setWinner(self, team: str):
        self.metadata.winner = team

    def write_json(self, print_reply):
        # Get Metadata
        retDict = self.metadata.__dict__
        # Add Lists of Initial Information
        retDict['initial_map_passability'] = self.initial_map_passability
        retDict['initial_map_metal'] = self.initial_map_metal
        retDict['initial_map_terraformed'] = self.initial_map_terraformed
        retDict['initial_map_visible'] = self.initial_map_visible
        # Add List
        turnDict = [i.__dict__ for i in self.turns]
        retDict['turns'] = turnDict
        # Return JSON
        retJson = json.dumps(retDict, separators=(',', ':'))
        if not print_reply:
            # create replay folder if needed
            path = pathlib.Path("replays/")
            path.mkdir(parents=True, exist_ok=True)

            # write the actual file
            with open(f"replays/{self.metadata.game_name}.awap23r", "w") as outfile:
                outfile.write(retJson)
        return retJson
