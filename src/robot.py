from src.game_constants import Direction, GameConstants, RobotType, TileState, Team
from src.map import Map
from src.info import RobotInfo
from dataclasses import dataclass

from src.errors import *

    
class Robot:
    # Static Variable
    counter = 1

    # Initial
    def __init__(self, row: int, col: int, team: Team, height: int, width: int, action_cost: int):
        self._name = f"robot_{self.count()}"
        self.increment()
        self._type = None
        self._row = row
        self._col = col
        self._team = team
        self._moved = True
        self._acted = True
        self._height = height
        self._width = width
        self._battery = GameConstants.INIT_BATTERY
        self._action_cost = action_cost

    @staticmethod
    def increment():
        Robot.counter += 1

    @staticmethod
    def count():
        return Robot.counter

    def get_battery(self) -> int:
        return self._battery

    def get_name(self) -> str:
        return self._name

    def get_type(self) -> RobotType:
        return self._type

    def get_coord(self) -> tuple[int, int]:
        return (self._row, self._col)

    def get_team(self) -> Team:
        return self._team

    def set_battery(self, battery) -> None:
        self._battery = battery

    def charge(self, charge: int) -> None:
        self._battery += charge
        self._battery = min(self._battery, GameConstants.INIT_BATTERY)

    def reset_move_status(self) -> None:
        self._moved = False

    def reset_acted_status(self) -> None:
        self._acted = False

    def make_move(self, move: Direction) -> bool:
        # Check Valid Move
        if (move == None):
            raise IllegalMoveInternalError(f"Move needs to be a direction {move}")
        newRow, newCol = self._row + move.value[0], self._col + move.value[1]
        # Check Move
        if (newRow < 0 or newRow >= self._height or newCol < 0 or newCol >= self._width):
            raise IllegalMoveInternalError(f"Move needs to be a direction {move}")
        # Check if already moved
        elif (self._moved):
            return False
        # Make Move
        self._moved = True
        self._row = newRow
        self._col = newCol
        return True

    def take_action(self, map: Map) -> list:
        raise Exception("take_action abstract method")

    def assert_can_take_action(self, map: Map):
        raise Exception("assert_can_take_action abstract method")

    def assert_ready_to_act(self):
        if (self._acted):
            raise IllegalActionError(f"{self._name} {self._row, self._col} has already acted")
        if self._battery < self._action_cost:
            raise IllegalActionError(f"{self._name} {self._row, self._col} has {self._battery}, needs {self._action_cost} battery")

    def info(self) -> RobotInfo:
        return RobotInfo(
            self._battery,
            self._acted,
            self._moved,
            self._action_cost, 
            self._row,
            self._col, 
            self._team,
            self._name, 
            self._type
        )

    def __str__(self) -> str:
        return f"{self._name} - ({self._row},{self._col}), {self._team}, B:{self._battery}"


class Miner_Robot(Robot):
    def __init__(self, row: int, col: int, team: Team, height: int, width: int, action_cost: int):
        Robot.__init__(self, row, col, team, height, width, action_cost)
        self._type = RobotType.MINER
        self._action_cost = GameConstants.MINER_ACTION_COST


    def assert_can_take_action(self, map: Map):
        self.assert_ready_to_act()

        if (map.get_tile_state(self._row, self._col, self._team) != TileState.MINING):
            raise IllegalActionError("Tried to mine on non-mining tile")

        return 


    def take_action(self, map: Map) -> list:
        self.assert_can_take_action(map)

        # Update Battery and Give Output
        self._acted = True
        self._battery -= self._action_cost
        return map.mine(self._row, self._col, self._team)


class Terraformer_Robot(Robot):
    def __init__(self, row: int, col: int, team: Team, height: int, width: int, action_cost: int):
        Robot.__init__(self, row, col, team, height, width, action_cost)
        self._type = RobotType.TERRAFORMER
        self._action_cost = GameConstants.TERRAFORMER_ACTION_COST


    def assert_can_take_action(self, map: Map):
        self.assert_ready_to_act()

        if (map.get_tile_state(self._row, self._col, self._team) != TileState.TERRAFORMABLE):
            raise IllegalActionError(f"Tried to terraform a non-terraformable tile at {self._row, self._col}")

        new_val = map._tiles[self._row][self._col].get_terraform()
        if self._team == Team.BLUE:
            new_val += 1
        else:
            new_val -= 1

        if not (-GameConstants.TERRAFORM_MAX <= new_val <= GameConstants.TERRAFORM_MAX):
            raise IllegalActionError(f"Tried to terraform a tile that has max terraform at {self._row, self._col}")



    def take_action(self, map: Map) -> list:
        self.assert_can_take_action(map)

        # Update Battery and Give Output
        self._acted = True
        self._battery -= self._action_cost
        map.terraform(self._row, self._col, self._team)

        v = map._tiles[self._row][self._col].get_terraform()
        if not (-GameConstants.TERRAFORM_MAX <= v <= GameConstants.TERRAFORM_MAX):
            raise Exception(f"bad {v} at {self._row, self._col}")

        return [self.get_coord()]


class Explorer_Robot(Robot):
    def __init__(self, row: int, col: int, team: Team, height: int, width: int, action_cost: int):
        Robot.__init__(self, row, col, team, height, width, action_cost)
        self._type = RobotType.EXPLORER
        self._action_cost = GameConstants.EXPLORER_ACTION_COST
        

    def assert_can_take_action(self, map: Map):
        self.assert_ready_to_act()

        def is_fog(x, y):
            return map._tiles[x][y].is_fog_of_war(self._team)

        has_fog = False
        for dx in range(-1, 2):
            for dy in range(-1, 2):
                nx, ny = self._row + dx, self._col + dy
                if 0 <= nx < map.get_height() and 0 <= ny < map.get_width():
                    if is_fog(nx, ny):
                        has_fog = True

        if not has_fog:
            raise IllegalActionError(f"Tried to explore, but no nearby tiles have fog at {self._row, self._col}")



    def take_action(self, map: Map) -> list:
        self.assert_can_take_action(map)

        # don't really need this check
        # if (map.get_tile_state(self._row, self._col, self._team) == TileState.IMPASSABLE):
        #     raise InvalidActionInternalError(f"Robot is on impassable tile {self._row, self._col}")

        # Update Battery and Give Output
        self._acted = True
        self._battery -= self._action_cost

        tiles = map.explore(self._row, self._col, self._team)
        return tiles
