from dataclasses import dataclass
from src.map import Map
from src.robot import Robot, Miner_Robot, Explorer_Robot, Terraformer_Robot, RobotInfo
from src.game_constants import Team, Direction, TileState, GameConstants, RobotType
from src.replay import Replay
from src.info import *
from src.errors import *
from collections import deque

class GameState:
    """ 
    Each turn, a GameState object is passed to players. 

    The GameState object should contain all information that players are 
    able to access about the state of the game.

    Note that if a player modifies the GameState object, it should not actually
    modify the true game state
    """

    def __init__(self, info : dict, red_robots : dict, blue_robots : dict, replay: Replay, map: Map):
        # General Game Information
        self.__map: Map = map
        self.__replay = replay
        self.__info = info

        # Robot Information
        self.__red_robots: dict[str, Robot] = red_robots
        self.__blue_robots: dict[str, Robot] = blue_robots

        # Player Cost Information
        self.__robot_spawn_cost = GameConstants.ROBOT_SPAWN_COST
        self.__robot_transform_cost = GameConstants.ROBOT_TRANSFORM_COST

    def __str__(self):
        """
        String representation of the GameState object
        """
        return f""

    def check_for_collision(self, row: int, col: int) -> RobotInfo:
        # Get current robots
        currTeam = self.__info.get("team")
        blue_robots = self.__blue_robots
        red_robots = self.__red_robots

        # Check if grid position is visible
        if self.__map.get_tile_state(row, col, currTeam) == TileState.ILLEGAL:
            return None

        # Check red and blue robots
        for robot_name in red_robots.keys():
            if (row, col) == red_robots.get(robot_name).get_coord():
                return red_robots.get(robot_name).info()
        for robot_name in blue_robots.keys():
            if (row, col) == blue_robots.get(robot_name).get_coord():
                return blue_robots.get(robot_name).info()

        # Otherwise return clear
        return None

    def optimal_path(self, startRow: int, startCol: int, endRow: int, endCol: int, checkCollisions=True) -> tuple[Direction,int]:
        '''
        Find the optimal path using BFS
        '''
        # Check if positions are valid
        currTeam = self.__info.get("team")
        startTile = self.__map.get_tile_state(startRow, startCol, currTeam)
        if (startTile == TileState.ILLEGAL or startTile == TileState.IMPASSABLE):
            return (None, -1)
        endTile = self.__map.get_tile_state(endRow, endCol, currTeam)
        if (endTile == TileState.ILLEGAL or endTile == TileState.IMPASSABLE):
            return (None, -1)

        # Otherwise, preform search
        visited = set()
        queue = deque([(None, startRow, startCol, 0)])
        while (queue):
            dir, queueRow, queueCol, moves = queue.popleft()
            if (endRow == queueRow and endCol == queueCol): return (dir, moves)
            for newDir in Direction:
                newRow, newCol = queueRow + \
                    newDir.value[0], queueCol + newDir.value[1]
                tileState = self.__map.get_tile_state(newRow, newCol, currTeam)
                # Check if its legal
                if (tileState == TileState.ILLEGAL or tileState == TileState.IMPASSABLE):
                    continue
                if (checkCollisions and self.check_for_collision(newRow, newCol) != None):
                    continue
                if ((newRow, newCol) not in visited):
                    if dir == None:
                        queue.append((newDir, newRow, newCol, moves+1))
                    else:
                        queue.append((dir, newRow, newCol, moves+1))
                    visited.add((newRow, newCol))

        # If we reached this point, a path to the co-ordinates isn't possible
        return (None, -1)

    def robot_to_base(self, robotName: str, checkCollisions=True) -> tuple[Direction,int]:
        '''
        Find the optimal path using BFS
        '''
        # Get current robots
        currTeam = self.__info.get("team")
        if (currTeam == Team.BLUE):
            robots = self.__blue_robots
        else:
            robots = self.__red_robots

        # Check if robot name is valid
        if (robots.get(robotName) == None):
            return (None,-1)
        currRobot = robots.get(robotName)

        # Check if position is valid
        startRow, startCol = currRobot.get_coord()
        startTile = self.__map.get_tile_state(startRow, startCol, currTeam)
        if (startTile == TileState.ILLEGAL or startTile == TileState.IMPASSABLE):
            return (None,-1)

        # Otherwise, preform search
        visited = set()
        queue = deque([(None, startRow, startCol, 0)])
        while (queue):
            dir, queueRow, queueCol, moves = queue.popleft()
            if (self.__map.is_terraformed(currTeam, queueRow, queueCol)):
                return (dir, moves)
            for newDir in Direction:
                newRow, newCol = queueRow + \
                    newDir.value[0], queueCol + newDir.value[1]
                tileState = self.__map.get_tile_state(newRow, newCol, currTeam)
                # Check if its legal
                if (tileState == TileState.ILLEGAL or tileState == TileState.IMPASSABLE):
                    continue
                if (checkCollisions and self.check_for_collision(newRow, newCol) != None):
                    continue
                if ((newRow, newCol) not in visited):
                    if dir == None:
                        queue.append((newDir, newRow, newCol, moves+1))
                    else:
                        queue.append((dir, newRow, newCol, moves+1))
                    visited.add((newRow, newCol))

        # If we reached this point, a path to a terraform tile isn't possible
        return (None, -1)


    def __assert_can_spawn_robot(self, type: RobotType, row: int, col: int):
        # Return False for incorrect move
        if (type == None):
            raise IllegalSpawnError(f"Invalid robot type {type}")

        # Get current robots
        currTeam = self.__info.get("team")

        # Check the tile for being terraformable
        spawnTile = self.__map.get_tile_state(row, col, currTeam)
        if (spawnTile == TileState.ILLEGAL or spawnTile == TileState.IMPASSABLE):
            raise IllegalSpawnError(f"Tried to spawn on illegal tile, type:{spawnTile} at {row, col}")
        if (not self.__map.is_terraformed(currTeam, row, col)):
            raise IllegalSpawnError(f"Tried to spawn on tile that isn't ally terraformed, status:{self.__map.get_terraform_status(row, col)} at {row, col}")
        if (self.check_for_collision(row, col) != None):
            raise IllegalSpawnError(f"Tried to spawn on occupied tile at {row, col}")

        # Check and preform metal cost
        my_metal = self.get_metal()
        if my_metal < self.get_spawn_cost(): 
            raise IllegalSpawnError(f"Not enough metal to spawn, has: {my_metal}, needs: {self.__robot_spawn_cost}")



    def can_spawn_robot(self, type: RobotType, row: int, col: int):
        try:
            self.__assert_can_spawn_robot(type, row, col)
        except IllegalSpawnError:
            return False
        return True


    def spawn_robot(self, type: RobotType, row: int, col: int) -> RobotInfo:
        # Get current robots
        currTeam = self.__info.get("team")
        robots = self.__get_ally_robots_obj()

        # Check and preform metal cost
        if (currTeam == Team.BLUE):
            field_name = "blue_metal"
        else:
            field_name = "red_metal"
        self.__info.update({field_name: self.get_metal() - self.__robot_spawn_cost})

        # Spawn robot
        new_robot = None
        if (type == RobotType.MINER):
            new_robot = Miner_Robot(
                row,
                col,
                currTeam,
                self.__map.get_height(),
                self.__map.get_width(),
                GameConstants.MINER_ACTION_COST
            )
        elif (type == RobotType.EXPLORER):
            new_robot = Explorer_Robot(
                row,
                col,
                currTeam,
                self.__map.get_height(),
                self.__map.get_width(),
                GameConstants.EXPLORER_ACTION_COST
            )
        else:
            new_robot = Terraformer_Robot(
                row,
                col,
                currTeam,
                self.__map.get_height(),
                self.__map.get_width(),
                GameConstants.TERRAFORMER_ACTION_COST
            )
        robots.update({new_robot.get_name() : new_robot})

        # Add Robot to Replay File and return
        self.__replay.add_robot_changes(new_robot, False)
        return new_robot.info()


    def __assert_can_robot_action(self, robotName: str) -> bool:
        robots = self.__get_ally_robots_obj()
        
        currRobot = robots.get(robotName)
        if currRobot is None:
            raise IllegalActionError(f"Unknown robot {robotName}")
        
        currRobot.assert_can_take_action(self.__map)



    def can_robot_action(self, robotName : str):
        try:
            self.__assert_can_robot_action(robotName)
        except IllegalActionError:
            return False
        return True


    def robot_action(self, robotName: str):
        self.__assert_can_robot_action(robotName)

        # Get current robots
        currTeam = self.get_team()
        robots = self.__get_ally_robots_obj()

        # Take robot action
        currRobot = robots.get(robotName)
        retList = currRobot.take_action(self.__map)


        # Change metal based on action
        if (currRobot.get_type() == RobotType.MINER):
            if (currTeam == Team.BLUE):
                self.__info.update({'blue_metal':self.__info.get('blue_metal') + retList[0]})
            else:
                self.__info.update({'red_metal':self.__info.get('red_metal') + retList[0]})
        elif (currRobot.get_type() == RobotType.TERRAFORMER):
            self.__replay.add_terraformed_tiles(retList)
        elif (currRobot.get_type() == RobotType.EXPLORER):
            self.__replay.add_explored_tiles(retList)
            

    def __assert_can_move_robot(self, robotName : str, move : Direction):
        # Return False for incorrect move
        if move is None:
            raise IllegalMoveError(f"Move must be in a valid direction, received:{move}")

        # Get current robots
        currTeam = self.get_team()
        robots = self.get_ally_robots()

        # Get Robot
        currRobot = robots.get(robotName)
        if currRobot is None:
            raise IllegalMoveError(f"Unknown robot {robotName}")

        # Check move validity
        row, col = currRobot.row, currRobot.col
        newRow, newCol = row + move.value[0], col + move.value[1]
        tile_state = self.__map.get_tile_state(newRow, newCol, currTeam)
        if tile_state == TileState.ILLEGAL:
            raise IllegalMoveError("Attempting to move into illegal tile")
        if tile_state == TileState.IMPASSABLE:
            raise IllegalMoveError("Attempting to move into impassable tile")


    def can_move_robot(self, robotName : str, move : Direction):
        try:
            self.__assert_can_move_robot(robotName, move)
        except IllegalMoveError:
            return False
        return True


    def move_robot(self, robotName: str, move: Direction) -> bool:
        self.__assert_can_move_robot(robotName, move)

        robots = self.__get_ally_robots_obj()

        currRobot = robots.get(robotName)
        row, col = currRobot.get_coord()
        newRow, newCol = row + move.value[0], col + move.value[1]

        # Check for collision
        altRobotInfo = self.check_for_collision(newRow, newCol)
        if (altRobotInfo != None):
            robots.pop(robotName)
            if (self.__blue_robots.get(altRobotInfo.name) != None):
                altRobot = self.__blue_robots.get(altRobotInfo.name)
                self.__blue_robots.pop(altRobotInfo.name)
            elif (self.__red_robots.get(altRobotInfo.name) != None):
                altRobot = self.__red_robots.get(altRobotInfo.name)
                self.__red_robots.pop(altRobotInfo.name)
            else:
                raise UnknownRobotInternalError(f"Unknown robot - {altRobotInfo}")
            # Remove robot in replay file
            self.__replay.add_robot_changes(currRobot, True)
            self.__replay.add_robot_changes(altRobot, True)
            return True

        # Preform Move
        result = currRobot.make_move(move)
        if (result):
            self.__replay.add_robot_changes(currRobot, False)
        return result


    def __assert_can_transform_robot(self, robotName : str, type : RobotType):

        # Return False for incorrect type
        if (type == None):
            raise IllegalTransformError(f"Invalid robot type {type}")

        robots = self.get_ally_robots()

        # Take robot action
        if (robots.get(robotName) == None):
            raise IllegalTransformError(f"Unknown robot {robotName}")

        my_metal = self.get_metal()
        if my_metal < self.__robot_transform_cost:
            raise IllegalTransformError(f"Not enough metal to transform, has: {my_metal}, needs: {self.__robot_transform_cost}")


    def can_transform_robot(self, robotName : str, type : RobotType):
        try:
            self.__assert_can_transform_robot(robotName, type)
        except IllegalTransformError:
            return False
        return True


    def transform_robot(self, robotName: str, type: RobotType) -> RobotInfo:

        self.__assert_can_transform_robot(robotName, type)
        

        # Get current robots
        currTeam = self.get_team()
        robots = self.__get_ally_robots_obj()

        currRobot = robots.get(robotName)

        # pay transform cost
        if (currTeam == Team.BLUE):
            field_name = "blue_metal"
        else:
            field_name = "red_metal"
        self.__info.update({field_name: self.get_metal() - self.__robot_spawn_cost})

        # Get current co-ordinates
        row, col = currRobot.get_coord()
        prevBattery = currRobot.get_battery()
        robots.pop(robotName)

        # Add Deleted Robot to Replay File
        self.__replay.add_robot_changes(currRobot, True)

        # Spawn robot and set battery
        new_robot = None
        if (type == RobotType.MINER):
            new_robot = Miner_Robot(
                row,
                col,
                currTeam,
                self.__map.get_height(),
                self.__map.get_width(),
                GameConstants.MINER_ACTION_COST
            )
        elif (type == RobotType.EXPLORER):
            new_robot = Explorer_Robot(
                row,
                col,
                currTeam,
                self.__map.get_height(),
                self.__map.get_width(),
                GameConstants.EXPLORER_ACTION_COST
            )
        else:
            new_robot = Terraformer_Robot(
                row,
                col,
                currTeam,
                self.__map.get_height(),
                self.__map.get_width(),
                GameConstants.TERRAFORMER_ACTION_COST
            )
        new_robot.set_battery(prevBattery)

        # Add New Robot to Replay File
        robots.update({new_robot.get_name() : new_robot})
        self.__replay.add_robot_changes(new_robot, False)
        return new_robot.info()


    def __get_ally_robots_obj(self):
        if self.get_team() == Team.BLUE:
            return self.__blue_robots
        else:
            return self.__red_robots



    """ GETTERS """

    def get_info(self):
        # State Game Info
        return GameInfo(
            ally_robots=self.get_ally_robots(),
            enemy_robots=self.get_enemy_robots(),
            map=self.get_map(),
            metal=self.get_metal(),
            team=self.get_team(),
            robot_spawn_cost=self.get_spawn_cost(),
            robot_transform_cost=self.get_transform_cost(),
            time_left=self.get_time_left(),
            turn=self.get_turn(),
        )


    def get_ally_robots(self) -> dict:
        # Get current robots
        if (self.get_team() == Team.BLUE):
            robots = self.__blue_robots
        else:
            robots = self.__red_robots

        # Get all robots
        retDict = {}
        for robot_name in robots.keys():
            retDict[robot_name] = robots.get(robot_name).info()
        return retDict

    def get_enemy_robots(self) -> dict:
        # Get current robots
        currTeam = self.get_team()
        if currTeam == Team.BLUE:
            enemy_robots = self.__red_robots
        else:
            enemy_robots = self.__blue_robots

        # Get all robots
        retDict = {}
        for robot_name in enemy_robots.keys():
            # Check if robots are visible
            row, col = enemy_robots.get(robot_name).get_coord()
            if (self.__map.get_tile_state(row, col, currTeam) != TileState.ILLEGAL):
                retDict[robot_name] = enemy_robots.get(robot_name).info()
        return retDict

    def get_str_map(self) -> list:
        currTeam = self.get_team()
        return self.__map.get_str_map(currTeam)

    def get_map(self) -> list:
        # Get CurrTeam and Map
        currTeam = self.get_team()
        currMap = self.__map.get_map(currTeam)
        # Add Robot Info
        currRobots = self.get_ally_robots()
        for robot in currRobots:
            info = currRobots[robot]
            row, col = info.row, info.col
            currMap[row][col].robot = info
        enemyRobots = self.get_enemy_robots()
        for robot in enemyRobots:
            info = enemyRobots[robot]
            row, col = info.row, info.col
            currMap[row][col].robot = info
        return currMap


    def get_metal(self):
        # Get Metal
        if self.get_team() == Team.BLUE:
            return self.__info.get("blue_metal")
        else:
            return self.__info.get("red_metal")

    def get_spawn_cost(self):
        return self.__robot_spawn_cost

    def get_transform_cost(self):
        return self.__robot_transform_cost

    def get_team(self):
        return self.__info.get("team")

    def get_turn(self):
        return self.__info.get("turn")

    def get_time_left(self):
        if self.get_team() == Team.BLUE:
            return self.__info.get("blue_time")
        else:
            return self.__info.get("red_time")
