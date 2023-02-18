# AWAP 2023 Game Engine

This is the AWAP 2023 game engine.

Last year's game engine can be found [here](https://github.com/rzhan11/awap2022-engine).

## Running Game Engine

To run the game engine, call the command:

`python3 run_game.py -m mapFile -b blueBotFile -r redBotFile -rp -sb -sr`

### Required arguments:

`-m` -> A map file located in the maps folder. (e.g. `map_1` where location: maps/map_1.json) (If a valid map file isn't given, a random map is generated for the game.)

`-b` -> A bot file (for blue bot) located in the bots folder. (e.g. `example_bot` where location: bots/example_bot.py)

`-r` -> A bot file (for red bot) located in the bots folder. (e.g. `example_bot` where location: bots/example_bot.py) 

OR

`-f` -> The path to a .json file that specifies the map, red bot, and blue bot (e.g. `game_settings.json`).

### Optional arguments:

`-rp` -> Replay_Print flag which prints replay file to stdout

`-sb` -> Silence_Blue flag which silences blue bot verbose

`-sr` -> Silence_Red flag which silences red bot verbose

### Example commands:

`python3 run_game.py -m main -b example_bot -r example_bot -rp`

`python3 run_game.py -m game_2 -b example_bot -r example_bot -rp -sb -sr`
