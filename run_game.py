"""
This file is responsible for reading in the game settings
and running the match.
"""
import argparse
from src.game import Game
from os import path
import json
from src.errors import *


def main():
    # Parser Arguements
    parser = argparse.ArgumentParser(description='Run Player Code')
    parser.add_argument("-m", "--map", help="map name")
    parser.add_argument("-b", "--blue_bot", help="blue bot name")
    parser.add_argument("-r", "--red_bot", help="red bot name")
    parser.add_argument('-rp', '--replay_print', action="store_true", help="print replay file to console")
    parser.add_argument('-sb', '--silence_blue', action='store_true', help="silence blue bot verbose")
    parser.add_argument('-sr', '--silence_red', action='store_true', help="silence red bot verbose")
    parser.add_argument('-f', '--file_input', help="read game settings (map, blueBot, redBot) from specified file")

    # Define Input through CLI
    currNamespace = parser.parse_args()

    
    if currNamespace.file_input is not None:
        # read map, blueBot,redBot from file
        with open(currNamespace.file_input) as f:
            settings = json.load(f)
            currNamespace.map = settings["map"]
            currNamespace.blue_bot = settings["blue_bot"]
            currNamespace.red_bot = settings["red_bot"]


    # if we are missing one of the required args, then alert user
    for val in ["map", "blue_bot", "red_bot"]:
        if getattr(currNamespace, val) is None:
            print(f"Please specify --{val}")
            exit(1)


    # Check Map File
    mapFile = f"maps/{currNamespace.map}.awap23m"

    # Check Blue Bot File
    blueBotFile = f"bots/{currNamespace.blue_bot}.py"
    if (not path.exists(blueBotFile)):
        raise InvalidBotFileError("Blue bot file not found")

    # Check Red Bot File
    redBotFile = f"bots/{currNamespace.red_bot}.py"
    if (not path.exists(redBotFile)):
        raise InvalidBotFileError("Red bot file not found")

    # Optional Commands
    print_reply = currNamespace.replay_print
    silence_blue = currNamespace.silence_blue
    silence_red = currNamespace.silence_red

    # Define game name for replay
    gameName = f"{currNamespace.blue_bot}-{currNamespace.red_bot}-{currNamespace.map}"

    # Get Game
    curr = Game(gameName, redBotFile, blueBotFile, mapFile, 
    print_reply=print_reply, silence_blue=silence_blue, silence_red=silence_red)
    replay = curr.run_game()
    if print_reply: print(replay)

if __name__ == "__main__":
    main()
