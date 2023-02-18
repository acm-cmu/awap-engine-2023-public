from src.game_constants import RobotType, Direction, Team, TileState
from src.game_state import GameState, GameInfo
from src.player import Player
from src.map import TileInfo, RobotInfo
import random
import numpy as np

class BotPlayer(Player):
    """
    Players will write a child class that implements (notably the play_turn method)
    """

    def getValue(self, x, y):
        if 0 <= x < self.explored.shape[0] and 0 <= y < self.explored.shape[1]:
            return self.explored[x][y]
        return True

    def explore(self, rob, rname, game_state):
        # get the current location

        x = rob.row
        y = rob.col
        """
        explored[x][y + 1], explored[x][y - 1],
        explored[x + 1][y], explored[x - 1][y],
        explored[x + 1][y + 1], explored[x - 1][y - 1],
        explored[x + 1][y - 1], explored[x - 1][y + 1]
        should all be true
        
        neighbours of (x + 1, y)
        (x + 2, y); (x + 2, y - 1); (x + 2, y + 1)
        
        neighbours of (x - 1, y)
        (x - 2, y); (x - 2, y - 1); (x - 2, y + 1)
        
        neighbours of (x, y + 1):
        (x, y + 2); (x - 1, y + 2); (x + 1, y + 2)
        
        neighbours of (x, y - 1):
        (x, y - 2); (x - 1, y - 2); (x + 1, y - 2)
        
        neighbour of (x + 1, y + 1):
        (x + 2, y + 2)
        
        neighbour of (x - 1, y - 1):
        (x - 2, y - 2)
        
        neighbour of (x - 1, y + 1):
        (x - 2, y + 2)
        
        neighbour of (x + 1, y - 1):
        (x + 2, y - 2)
        """

        if (not self.getValue(x + 2, y) or
                not self.getValue(x + 2, y - 1) or
                not self.getValue(x + 2, y + 1)):
            self.set_explored_true(x + 1, y)
            game_state.move_robot(rname, Direction.DOWN)
        elif (not self.getValue(x - 2, y) or
                not self.getValue(x - 2, y - 1) or
                not self.getValue(x - 2, y + 1)):
            self.set_explored_true(x - 1, y)
            game_state.move_robot(rname, Direction.UP)
        elif (not self.getValue(x, y + 2) or
                not self.getValue(x - 1, y + 2) or
                not self.getValue(x + 1, y + 2)):
            self.set_explored_true(x, y + 1)
            game_state.move_robot(rname, Direction.RIGHT)
        elif (not self.getValue(x, y - 2) or
                not self.getValue(x - 1, y - 2) or
                not self.getValue(x + 1, y - 2)):
            self.set_explored_true(x, y - 1)
            game_state.move_robot(rname, Direction.LEFT)
        elif not self.getValue(x + 2, y + 2):
            self.set_explored_true(x + 1, y + 1)
            game_state.move_robot(rname, Direction.DOWN_RIGHT)
        elif not self.getValue(x - 2, y - 2):
            self.set_explored_true(x - 1, y - 1)
            game_state.move_robot(rname, Direction.UP_LEFT)
        elif not self.getValue(x + 2, y - 2):
            self.set_explored_true(x + 1, y - 1)
            game_state.move_robot(rname, Direction.DOWN_LEFT)
        elif not self.getValue(x - 2, y + 2):
            self.set_explored_true(x - 1, y + 1)
            game_state.move_robot(rname, Direction.UP_RIGHT)
    def set_explored_true(self, x, y):

        for i in range(-1, 2):
            for j in range(-1, 2):
                x1 = x + i
                y1 = y + j
                if 0 <= x1 < self.explored.shape[0] and 0 <= y1 < self.explored.shape[1]:
                    self.explored[x1][y1] = True

    def __init__(self, team: Team):
        self.team = team
        self.explored = None
        self.first_time = True
        return

    def play_turn(self, game_state: GameState) -> None:

        # get info
        ginfo = game_state.get_info()

        # get turn/team info
        height, width = len(ginfo.map), len(ginfo.map[0])
        if self.explored is None:
            self.explored = np.ndarray(dtype=bool, shape=(height, width))

        # print info about the game
        print(f"Turn {ginfo.turn}, team {ginfo.team}")
        print("Map height", height)
        print("Map width", width)

        # find un-occupied ally tile
        ally_tiles = []
        for row in range(height):
            for col in range(width):
                # get the tile at (row, col)
                tile = ginfo.map[row][col]
                # skip fogged tiles
                if tile is not None:  # ignore fogged tiles
                    if tile.robot is None:  # ignore occupied tiles
                        if tile.terraform > 0:  # ensure tile is ally-terraformed
                            ally_tiles += [tile]
                            self.explored[row][col] = True
        print("Ally tiles", ally_tiles)

        # spawn on a random tile
        print(f"My metal {game_state.get_metal()}")
        if len(ally_tiles) > 0:
            # pick a random one to spawn on
            spawn_loc = random.choice(ally_tiles)
            spawn_type = random.choice([RobotType.MINER, RobotType.EXPLORER, RobotType.TERRAFORMER])
            # spawn the robot
            print(f"Spawning robot at {spawn_loc.row, spawn_loc.col}")
            # check if we can spawn here (checks if we can afford, tile is empty, and tile is ours)
            if game_state.can_spawn_robot(spawn_type, spawn_loc.row, spawn_loc.col):
                game_state.spawn_robot(spawn_type, spawn_loc.row, spawn_loc.col)

        # move robots
        robots = game_state.get_ally_robots()

        # iterate through dictionary of robots
        for rname, rob in robots.items():
            print(f"Robot {rname} at {rob.row, rob.col}")
            if rob.type == RobotType.EXPLORER:
                self.explore(rob, rname, game_state)
                return
            # randomly move if possible
            all_dirs = [dir for dir in Direction]
            move_dir = random.choice(all_dirs)

            # check if we can move in this direction
            if game_state.can_move_robot(rname, move_dir):
                # try to not collide into robots from our team
                dest_loc = (rob.row + move_dir.value[0], rob.col + move_dir.value[1])
                dest_tile = game_state.get_map()[dest_loc[0]][dest_loc[1]]

                if dest_tile.robot is None or dest_tile.robot.team != self.team:
                    game_state.move_robot(rname, move_dir)

            # action if possible
            if game_state.can_robot_action(rname):
                game_state.robot_action(rname)


