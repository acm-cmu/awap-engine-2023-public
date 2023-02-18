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
                not self.getValue(x + 2, y + 1)) and game_state.can_move_robot(rname, Direction.DOWN):
            self.set_explored_true(x + 1, y, game_state)
            print(rname, " going down")
            game_state.move_robot(rname, Direction.DOWN)
        elif (not self.getValue(x - 2, y) or
                not self.getValue(x - 2, y - 1) or
                not self.getValue(x - 2, y + 1)) and game_state.can_move_robot(rname, Direction.UP):
            self.set_explored_true(x - 1, y, game_state)
            print(rname, " going up")
            game_state.move_robot(rname, Direction.UP)
        elif (not self.getValue(x, y + 2) or
                not self.getValue(x - 1, y + 2) or
                not self.getValue(x + 1, y + 2)) and game_state.can_move_robot(rname, Direction.RIGHT):
            self.set_explored_true(x, y + 1, game_state)
            print(rname, " going right")
            game_state.move_robot(rname, Direction.RIGHT)

        elif (not self.getValue(x, y - 2) or
                not self.getValue(x - 1, y - 2) or
                not self.getValue(x + 1, y - 2)) and game_state.can_move_robot(rname, Direction.LEFT):
            self.set_explored_true(x, y - 1, game_state)
            print(rname, " going left")
            game_state.move_robot(rname, Direction.LEFT)
        elif not self.getValue(x + 2, y + 2) and game_state.can_move_robot(rname, Direction.DOWN_RIGHT):
            self.set_explored_true(x + 1, y + 1, game_state)
            print(rname, " going down right")
            game_state.move_robot(rname, Direction.DOWN_RIGHT)
        elif not self.getValue(x - 2, y - 2) and game_state.can_move_robot(rname, Direction.UP_LEFT):
            self.set_explored_true(x - 1, y - 1, game_state)
            print(rname, " going up left")
            game_state.move_robot(rname, Direction.UP_LEFT)
        elif not self.getValue(x + 2, y - 2) and game_state.can_move_robot(rname, Direction.DOWN_LEFT):
            self.set_explored_true(x + 1, y - 1, game_state)
            game_state.move_robot(rname, Direction.DOWN_LEFT)
        elif not self.getValue(x - 2, y + 2) and game_state.can_move_robot(rname, Direction.UP_RIGHT):
            self.set_explored_true(x - 1, y + 1, game_state)
            game_state.move_robot(rname, Direction.UP_RIGHT)
        else:
            # random move anywhere
            all_dirs = [dir for dir in Direction]
            for d in all_dirs:
                if game_state.can_move_robot(rname, d):
                    game_state.move_robot(rname, d)
                    break

        if game_state.can_robot_action(rname):
            game_state.robot_action(rname)

    def set_explored_true(self, x, y, game_state):
        for i in range(-1, 2):
            for j in range(-1, 2):
                x1 = x + i
                y1 = y + j
                if 0 <= x1 < self.explored.shape[0] and 0 <= y1 < self.explored.shape[1]:
                    tile = game_state.get_map()[x1][y1]
                    if tile is not None and tile.mining and tile.mining > 0:
                        self.deposit_tiles[(x1, y1)] = tile.mining
                    elif tile is not None and tile.terraform and 10 > tile.terraform >= -10:
                        self.terraformable_tiles[(x1, y1)] = tile.terraform
                    self.explored[x1][y1] = True

    def __init__(self, team: Team):
        self.deposit_tiles = {}
        self.terraformable_tiles = {}
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
            if self.first_time or len(self.deposit_tiles) == 0:
                spawn_type = RobotType.EXPLORER
                self.first_time = False
            else:
                spawn_type = random.choice([RobotType.MINER, RobotType.EXPLORER, RobotType.TERRAFORMER])
            # spawn the robot

            # check if we can spawn here (checks if we can afford, tile is empty, and tile is ours)
            if game_state.can_spawn_robot(spawn_type, spawn_loc.row, spawn_loc.col):
                r = game_state.spawn_robot(spawn_type, spawn_loc.row, spawn_loc.col)
                print(f"Spawning robot at {spawn_loc.row, spawn_loc.col} which is {r.type}")
        # move robots
        robots = game_state.get_ally_robots()

        # iterate through dictionary of robots
        for rname, rob in robots.items():
            print(f"Robot {rname} at {rob.row, rob.col}")
            if rob.type == RobotType.EXPLORER:
                self.explore(rob, rname, game_state)
            else:
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


