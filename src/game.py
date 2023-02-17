"""
This file is responsible to the execution of a game
"""
from src.player import Player
from src.game_constants import Team
from src.game_state import GameState
from src.replay import Replay
from src.robot import Robot
from src.map import Map
from src.game_constants import GameConstants
import importlib.util
import sys
from contextlib import contextmanager
import os
from threading import Thread
import time

# Global Functions
@contextmanager
def suppress_stdout():
    with open(os.devnull, "w") as devnull:
        old_stdout = sys.stdout
        sys.stdout = devnull
        try:
            yield
        finally:
            sys.stdout = old_stdout

def import_file(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    sys.modules[module_name] = module
    return module

class Game:
    def __init__(self, game_name, red_path, blue_path, map_path, print_reply=False, silence_blue=True, silence_red=True):
        """
        Initializes players

        Args:
            p1_path (_type_): path to player 1's file
            p2_path (_type_): path to player 2's file
        """

        # initialize map
        self.map = Map(map_path, radius=GameConstants.BASE_VISIBLE_RADIUS)

        # General Game Variables
        self.winner = None
        self.max_turns = GameConstants.NUM_TURNS
        self.robot_charge = GameConstants.ROBOT_CHARGE
        self.passive_metal = GameConstants.METAL_GAINED_PER_TURN
        self.silence_blue = silence_blue
        self.silence_red = silence_red
        self.print_reply = print_reply

        # Robot Names
        map_name = map_path.split('/')[1].split(".")[0]
        red_robot_name = red_path.split('/')[1].split(".")[0]
        blue_robot_name = blue_path.split('/')[1].split(".")[0]

        # replay info
        self.replay = Replay(
            game_name,
            map_name,
            self.map.get_height(),
            self.map.get_width(),
            red_robot_name,
            blue_robot_name,
            GameConstants.INIT_METAL,
            self.map.initial_map_passability,
            self.map.initial_map_metal,
            self.map.initial_map_terraformed,
            self.map.initial_map_visible
        )

        # initialize game state variables
        self.info = {}
        self.info.update({"team":Team.BLUE})
        self.info.update({"red_metal":GameConstants.INIT_METAL})
        self.info.update({"blue_metal":GameConstants.INIT_METAL})
        self.info.update({"red_time":GameConstants.TIME_LIMIT})
        self.info.update({"blue_time":GameConstants.TIME_LIMIT})
        self.info.update({"turn":1})
        self.red_robots = {}
        self.blue_robots = {}
        self.game_state = GameState(self.info, self.red_robots, self.blue_robots, self.replay, self.map)
        
        # initialize players
        self.blue_player: Player = import_file(
            f"bots.{blue_robot_name}", blue_path).BotPlayer(Team.BLUE)
        self.red_player: Player = import_file(
            f"bots.{red_robot_name}", red_path).BotPlayer(Team.RED)

    def get_curr_team(self) -> Team:
        return self.info.get("team")

    def run_game(self) -> Replay:
        """
        Runs an entire game, using the specified object
        """
        # Play all turns
        for turn in range(1, self.max_turns+1):
            # Play Blue Team's Turn
            self.info.update({"team":Team.BLUE})
            timeout = self.run_turn(turn, self.blue_player)
            if timeout: # Declare Red Winner on Timeout
                self.replay.setWinner("red")
                if not (self.silence_blue and self.silence_red): 
                    print(f"Winner: {self.replay.metadata.winner} By Timeout")
                return self.replay.write_json(self.print_reply)
            # Play Red Team's Turn
            self.info.update({"team":Team.RED})
            timeout = self.run_turn(turn, self.red_player)
            if timeout: # Declare Blue Winner on Timeout
                self.replay.setWinner("blue")
                if not (self.silence_blue and self.silence_red): 
                    print(f"Winner: {self.replay.metadata.winner} By Timeout")
                return self.replay.write_json(self.print_reply)

        # Calculate Terra Tiles
        red_terra_tiles = 0
        blue_terra_tiles = 0
        for row in range(self.map.get_height()):
            for col in range(self.map.get_width()):
                if (self.map.is_terraformed(Team.BLUE, row, col)):
                    blue_terra_tiles += 1
                elif (self.map.is_terraformed(Team.RED, row, col)):
                    red_terra_tiles += 1

        # Calculate Number of Robots
        red_robots = len(self.red_robots.keys())
        blue_robots = len(self.blue_robots.keys())

        # Calculate Metal
        red_metal = self.info.get('red_metal')
        blue_metal = self.info.get('blue_metal')

        # Calculate Time
        red_time = self.info.get('red_time')
        blue_time = self.info.get('blue_time')

        # Check
        if (red_terra_tiles > blue_terra_tiles):
            self.replay.setWinner("red")
        elif (blue_terra_tiles > red_terra_tiles):
            self.replay.setWinner("blue")
        elif (red_robots > blue_robots):
            self.replay.setWinner("red")
        elif (blue_robots > red_robots):
            self.replay.setWinner("blue")
        elif (red_metal > blue_metal):
            self.replay.setWinner("red")
        elif (blue_metal > red_metal):
            self.replay.setWinner("blue")
        elif (red_time < blue_time):
            self.replay.setWinner("red")
        elif (blue_time < red_time):
            self.replay.setWinner("blue")
        else:
            # red wins by default
            self.replay.setWinner("red")

        # Save Replay File
        if not (self.silence_blue and self.silence_red):
            print(f"Winner: {self.replay.metadata.winner}")
        retJson = self.replay.write_json(self.print_reply)
        return retJson

    def run_turn(self, turn: int, player: Player) -> bool:
        """
        Runs a single turn of the game
        Calls each player's "play_turn" once to get their actions
        Processes their actions

        Treats time-outs appropriately
        """
        # Get Team and update turn left
        team = self.info.get("team")
        self.info.update({"turn":turn})

        # Check Team
        if (team == Team.RED):
            robots = self.red_robots
            player = self.red_player
            time_left = self.info.get('red_time')
        else:
            robots = self.blue_robots
            player = self.blue_player
            time_left = self.info.get('blue_time')

        # start gaining passive metal after round one
        if turn > 1:
            if team == Team.RED:
                self.info.update({'red_metal':self.info.get('red_metal') + self.passive_metal})
            else:
                self.info.update({'blue_metal':self.info.get('blue_metal') + self.passive_metal})


        # Update Robots Battery on Terraform Tiles
        for robot_name in robots.keys():
            currRobot : Robot = robots.get(robot_name)
            currRobot.reset_acted_status()
            currRobot.reset_move_status()
            row, col = currRobot.get_coord()
            if (self.map.is_terraformed(team, row, col)):
                currRobot.charge(self.robot_charge)

        # Suppress Print
        if(team == Team.BLUE and self.silence_blue):
            stdout = sys.stdout
            sys.stdout = open(os.devnull, "w")
        if(team == Team.RED and self.silence_red):
            stdout = sys.stdout
            sys.stdout = open(os.devnull, "w")
        
        # Run Thread
        thread = Thread(target=player.play_turn, args=[self.game_state], daemon=True)
        funcTime = time.time()
        thread.start()      
        thread.join(time_left)
        funcTime = time.time() - funcTime

        # Restore Print
        if(team == Team.BLUE and self.silence_blue):
            sys.stdout = stdout
        if(team == Team.RED and self.silence_red):
            sys.stdout = stdout

        # If there is still time left, automatically lose on timeout
        if thread.is_alive() or funcTime >= time_left:
            if (team == Team.RED): replay_team = "red"
            else: replay_team = "blue"
            self.replay.addTurn(replay_team, -1, turn, -1, timeout=True)
            return True

        # Change Replay File
        if (team == Team.RED):
            replay_team = "red"
            metal = self.info.get('red_metal')
            self.info.update({'red_time':self.info.get('red_time') - funcTime})
            time_left = self.info.get('red_time')
        else:
            replay_team = "blue"
            metal = self.info.get('blue_metal')
            self.info.update({'blue_time':self.info.get('blue_time') - funcTime})
            time_left = self.info.get('blue_time')

        # Turn Details
        self.replay.addTurn(replay_team, time_left, len(robots), turn, metal)
        return False
