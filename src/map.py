from src.game_constants import Team, TileState, GameConstants, RobotType, Direction
from random import random, randint, choice, shuffle
from collections import deque
import copy
import json
from os.path import isfile
from src.info import RobotInfo, TileInfo
from src.errors import *
from src.map_validate import val_map_wrap


class Tile:
    def __init__(self, state: TileState, row : int, col : int, fog_of_war_blue : bool,
    fog_of_war_red : bool, terraform : int, mining : int):
        self._state = state
        self._row = row
        self._col = col
        self._terraform = terraform
        self._fog_of_war_blue = fog_of_war_blue
        self._fog_of_war_red = fog_of_war_red
        self._mining = mining

    def get_row(self) -> int:
        return self._row

    def get_col(self) -> int:
        return self._col

    def get_state(self) -> TileState:
        return self._state

    def get_terraform(self) -> int:
        return self._terraform

    def get_mining(self) -> int:
        return self._mining

    def get_fog_of_war(self, team:Team) -> bool:
        if team == Team.BLUE:
            return self._fog_of_war_blue
        else:
            return self._fog_of_war_red

    def is_fog_of_war(self, team : Team) -> bool:
        if(team == Team.BLUE):
            return self._fog_of_war_blue
        else:
            return self._fog_of_war_red

    def terraform(self, team: Team) -> bool:
        if team == Team.BLUE:
            if(self._terraform >= GameConstants.TERRAFORM_MAX): return False
            self._terraform += 1
        else:
            if(self._terraform <= -GameConstants.TERRAFORM_MAX): return False
            self._terraform -= 1
        return True 

    def explore(self, team: Team) -> bool:
        if team == Team.BLUE and self._fog_of_war_blue:
            self._fog_of_war_blue = False
            return True
        elif team == Team.RED and self._fog_of_war_red:
            self._fog_of_war_red = False
            return True
        return False

    def string(self, team: Team) ->  str:
        tileInfo = self.get_info(team)
        if tileInfo == None:
            return "#"
        elif tileInfo.state == TileState.TERRAFORMABLE:
            return str(tileInfo.terraform)
        elif tileInfo.state == TileState.MINING:
            return "M"
        elif tileInfo.state == TileState.IMPASSABLE:
            return "I"
        else:
            raise InvalidTileStateInternalError(f"{tileInfo.state}")

    def get_info(self, team: Team) -> TileInfo:
        # Return none for fog of war
        if team == Team.BLUE and self._fog_of_war_blue:
            return None
        elif team == Team.RED and self._fog_of_war_red:
            return None
        # Otherwise, Return TileInfo
        if team == Team.RED: 
            return TileInfo(self._state,self._row,self._col,self._terraform*-1,self._mining,None)
        else: 
            return TileInfo(self._state,self._row,self._col,self._terraform,self._mining,None)

    def __str__(self) -> str:
        if self._state == TileState.TERRAFORMABLE:
            return str(self._terraform)
        elif self._state == TileState.MINING:
            return "M"
        elif self._state == TileState.IMPASSABLE:
            return "I"
        else:
            raise InvalidTileStateInternalError(f"{self.state}")

    def copy(self):
        """
        Creates a deep copy of this object
        """
        return copy.copy(self)


class Map:
    def __init__(self, path: str = None, radius = 1):
        # Check Tiles Safety
        if isfile(path):
            with open(path) as f:
                normList = json.load(f)
            val_map_wrap(normList)

            self._tiles = MapReader.generateMap(normList,radius=radius)
        else:
            self._tiles = MapReader.generateRandMap(GameConstants.MAX_MAP_HEIGHT,GameConstants.MAX_MAP_WIDTH, radius=radius)
            MapReader.saveMap(self._tiles, path.split('/')[1].split(".")[0])            

        # Store Variables
        self._height = len(self._tiles)
        self._width = len(self._tiles[0])

        # Store All Initial Map Lists
        self.initial_map_passability = []
        self.initial_map_metal = []
        self.initial_map_terraformed = []
        self.initial_map_visible = []
        for row in range(self._height):
            for col in range(self._width):
                tile = self._tiles[row][col]
                # Add Map Config
                if tile.get_state() == TileState.IMPASSABLE:
                    self.initial_map_passability.append((row,col))
                elif tile.get_state() == TileState.MINING:
                    self.initial_map_metal.append((row,col,tile.get_mining()))
                elif tile.get_terraform() != 0:
                    self.initial_map_terraformed.append((row,col,tile.get_terraform()))
                # Add Fog of War
                if not tile.get_fog_of_war(Team.RED):
                    self.initial_map_visible.append((row,col,1))
                if not tile.get_fog_of_war(Team.BLUE):
                    self.initial_map_visible.append((row,col,2))

    def get_height(self) -> int:
        return self._height

    def get_width(self) -> int:
        return self._width

    def is_terraformed(self, team: Team, row: int, col: int) -> bool:
        if (row < 0 or row >= self._height or col < 0 or col >= self._width):
            return None
        terraform = self._tiles[row][col].get_terraform()
        if (team == Team.RED): return terraform < 0
        else: return terraform > 0

    def is_mineable(self, row: int, col: int) -> bool:
        if (row < 0 or row >= self._height or col < 0 or col >= self._width):
            return None
        return self._tiles[row][col].get_state() == TileState.MINING

    def get_tile_state(self, row: int, col: int, team: Team) -> TileState:
        if (row < 0 or row >= self._height or col < 0 or col >= self._width):
            return TileState.ILLEGAL
        if (self._tiles[row][col].is_fog_of_war(team)):
            return TileState.ILLEGAL
        return self._tiles[row][col].get_state()

    def get_terraform_status(self, row: int, col: int) -> int:
        return self._tiles[row][col].get_terraform()

    def terraform(self, row: int, col: int, team : Team) -> bool:
        """
        Changes Map State
        """
        if (row < 0 or row >= self._height or col < 0 or col >= self._width):
            return None
        
        # Check correct co-ordinates
        if (self.get_tile_state(row,col,team) == TileState.ILLEGAL):
            raise TerraformInternalError(f"Illegal coordinate {row, col, team}")

        # Get Tile
        tile = self._tiles[row][col]
        tstate = tile.get_state()
        if (tstate != TileState.TERRAFORMABLE):
            raise TerraformInternalError(f"Not a terraformable tile {row, col} {tstate}")

        # Terraform Tile
        return tile.terraform(team)

    def explore(self, row: int, col: int, team : Team) -> list:
        if (row < 0 or row >= self._height or col < 0 or col >= self._width):
            return None
        
        # Check correct co-ordinates
        if (self.get_tile_state(row,col,team) == TileState.ILLEGAL):
            raise ExploreInternalError(f"Illegal coordinate {row, col, team}")

        # Get Tile
        tile = self._tiles[row][col]
        tstate = tile.get_state()
        if (tstate == TileState.IMPASSABLE):
            raise ExploreInternalError(f"Impassable tile {row, col}")


        # Terraform Tile
        exploredTiles = []
        for addRow in range(-1, 2):
            for addCol in range(-1, 2):
                newRow, newCol = row + addRow, col + addCol
                if (0 <= newCol < self._width and 0 <= newRow < self._height):
                    newtile = self._tiles[newRow][newCol]
                    if(newtile.explore(team)):
                        exploredTiles.append((newRow,newCol))
        return exploredTiles

    def mine(self, row: int, col: int, team : Team) -> list:
        if (row < 0 or row >= self._height or col < 0 or col >= self._width):
            raise MineInternalError(f"Tile not on map {row, col}")
        
        # Check correct co-ordinates
        tstate = self.get_tile_state(row,col,team)
        if (tstate == TileState.ILLEGAL):
            raise MineInternalError(f"Illegal tile {row, col, team}")

        # Get Tile
        tile = self._tiles[row][col]
        if (tile.get_state() != TileState.MINING): return []
        
        # Return Mining
        return [tile.get_mining()]

    def get_str_map(self, team: Team) -> list[list[str]]:
        retList = []
        for row in range(self._height):
            tileStr = []
            for col in range(self._width):
                tileStr.append(self._tiles[row][col].string(team))
            retList.append(tileStr)
        return retList

    def get_map(self, team: Team) -> list[list[TileInfo]]:
        retList = []
        for row in range(self._height):
            tileStr = []
            for col in range(self._width):
                tileStr.append(self._tiles[row][col].get_info(team))
            retList.append(tileStr)
        return retList

    def __str__(self) -> str:
        retList = []
        for row in range(self._height):
            tileStr = []
            for col in range(self._width):
                tileStr.append(self._tiles[row][col].__str__())
            retList.append("\t".join(tileStr))
        return "\n".join(retList)

class MapReader: 
    # Generate a map
    @staticmethod
    def generateMap(arr : list[list[tuple[str,int,int]]], radius=1) -> list[list[Tile]]:
        #Check Arguments
        if type(arr) != list:
            raise InvalidMapError(f"Map does not follow format, should be list[list[tuple[str,int,int]]]")
        if len(arr) == 0 or len(arr[0]) == 0:
            raise InvalidMapError(f"Map width/height need to be nonzero w:{len(arr)} h:{len(arr[0])}")

        height, width = len(arr), len(arr[0])
        
        for row in range(height):
            for col in range(width):
                typs = tuple(type(x) for x in arr[row][col])
                if typs != (str, int, int):
                    raise InvalidMapError(f"Map file elements need to be (str, int, int), received {typs}:{arr[row][col]} at {row, col}")


        #Populate Tiles
        retTiles = [[None for col in range(width)] for row in range(height)]
        for row in range(height):
            for col in range(width):
                #Get Tile State
                if(arr[row][col][0] == "T"): tilestate = TileState.TERRAFORMABLE
                elif(arr[row][col][0] == "I"): tilestate = TileState.IMPASSABLE
                elif(arr[row][col][0] == "M"): tilestate = TileState.MINING
                else:
                    raise InvalidMapError(f"Invalid tile state `{arr[row][col][0]}` at {row, col}")

                #Get Other Variables
                terraform = arr[row][col][1]
                mining = arr[row][col][2]

                # Check Terraform Variable
                if(terraform != 0 and tilestate != TileState.TERRAFORMABLE):
                    raise InvalidMapError(f"Non-terraform tile has terraform status `{terraform}` at {row, col}")

                # Check Mining Variable
                if(mining < 0): 
                    raise InvalidMapError(f"Tile has negative mining `{mining}` at {row, col}")
                if(mining > 0 and tilestate != TileState.MINING):
                    raise InvalidMapError(f"Non-mining tile has nonzero mining `{mining}` at {row, col}")
                
                # Set Tile
                if terraform > 0:
                    retTiles[row][col] = Tile(tilestate, row, col, False, True, terraform, mining)
                elif terraform < 0:
                    retTiles[row][col] = Tile(tilestate, row, col, True, False, terraform, mining)
                else:
                    retTiles[row][col] = Tile(tilestate, row, col, True, True, terraform, mining)

        #Return Tiles
        MapReader.visualizeBaseTiles(retTiles,radius=radius)
        return retTiles

    @staticmethod
    def visualizeBaseTiles(retTiles : list[list[Tile]], radius=1):
        # Use Height and Width
        height, width = len(retTiles), len(retTiles[0])
        if(width <= 0 or height <= 0):
            print("0-dimension tiles given")
            raise EnvironmentError

        # Explore Function
        def explore(row : int, col : int, team : Team) -> None:
            visited = set()
            queue = deque([(row, col, radius)])
            visited.add((row,col))
            while (queue):
                queueRow, queueCol, depth = queue.popleft()
                retTiles[queueRow][queueCol].explore(team)
                if(depth == 0): continue
                for newDir in Direction:
                    newRow, newCol = queueRow + newDir.value[0], queueCol + newDir.value[1]
                    if 0 <= newRow < height and 0 <= newCol < width and (newRow,newCol) not in visited:
                        queue.append((newRow, newCol, depth-1))
                        visited.add((newRow,newCol))

        # Now Explore
        for row in range(height):
            for col in range(width):
                tile = retTiles[row][col]
                if tile.get_terraform() > 0:
                    explore(row,col,Team.BLUE)
                elif tile.get_terraform() < 0:
                    explore(row,col,Team.RED)

        return

    # Generate a random map
    @staticmethod
    def makeReflectTile(width : int, height : int, row : int, col : int, type="diagonal"):
        if(width <= 0 or height <= 0 or not(0 <= row < height) or not(0 <= col < width)):
            print("Invalid dimensions given")
            raise EnvironmentError
        # Give new row and column
        if type == "diagonal":
            return width - 1 - row, height - 1 - col
        elif type == "horizontal":
            return row, height - 1 - col
        elif type == "vertical":
            return width - 1 - row, col
        else:
            print("Invalid reflections given")
            raise EnvironmentError

    # Generate a random map
    @staticmethod
    def generateRandMap(width : int, height : int, impassRatio = 0.2, mineRatio = 0.2, baseRatio = 0.15, radius=1) -> list[list[Tile]]:
        # Check Dimensions
        if (width <= 0 or height <= 0):
            raise InvalidMapError(f"generateRandMap - invalid width/height given, w:{width} h:{height}")

        # Check Reflection Type
        reflect = choice(["diagonal","horizontal","vertical"])
        tiles = [(row,col) for col in range(width) for row in range(height)]
        shuffle(tiles)

        #Populate Tiles
        retTiles = [[Tile(TileState.TERRAFORMABLE, row, col, True, True, 0, 0) for col in range(width)] for row in range(height)]

        #Add Impass Tiles
        impassTiles = int(width*height*impassRatio/2)
        for row, col in tiles[:impassTiles]:
            altRow, altCol = MapReader.makeReflectTile(width,height,row,col,type=reflect)
            retTiles[row][col] = Tile(TileState.IMPASSABLE, row, col, True, True, 0, 0)
            retTiles[altRow][altCol] = Tile(TileState.IMPASSABLE, altRow, altCol, True, True, 0, 0)

        #Add Mine Tiles
        mineTiles = int(width*height*mineRatio/2)
        for row, col in tiles[impassTiles:impassTiles+mineTiles]:
            altRow, altCol = MapReader.makeReflectTile(width,height,row,col,type=reflect)
            mineNum = randint(GameConstants.MINING_MIN,GameConstants.MINING_MAX)
            retTiles[row][col] = Tile(TileState.MINING, row, col, True, True, 0, mineNum)
            retTiles[altRow][altCol] = Tile(TileState.MINING, altRow, altCol, True, True, 0, mineNum)

        #Add Bases
        terraTiles = int(width*height*baseRatio/2)
        for row, col in tiles[impassTiles+mineTiles:impassTiles+mineTiles+terraTiles]:
            altRow, altCol = MapReader.makeReflectTile(width,height,row,col,type=reflect)
            retTiles[row][col] = Tile(TileState.TERRAFORMABLE, row, col, False, True, 5, 0)
            retTiles[altRow][altCol] = Tile(TileState.TERRAFORMABLE, altRow, altCol, True, False, -5, 0)
            
        #Return Tiles
        MapReader.visualizeBaseTiles(retTiles,radius=radius)
        return retTiles

    # Save a map from input
    @staticmethod
    def saveMap(tiles : list[list[Tile]], name : str) -> None:
        # Check Values
        if(len(tiles) == 0 or type(tiles[0]) != list or 
        len(tiles[0]) == 0 or type(tiles[0][0]) != Tile):
            raise InvalidMapError("Invalid element type in list for Generate Map")

        # Save Map
        height, width = len(tiles), len(tiles[0])
        saveArr = []
        for row in range(height):
            tempArr = []
            for col in range(width):
                tileStr = ""
                tile = tiles[row][col]
                tstate = tile.get_state()
                if tstate == TileState.IMPASSABLE: tileStr = "I"
                elif tstate == TileState.MINING: tileStr = "M"
                elif tstate == TileState.TERRAFORMABLE: tileStr = "T"
                else:
                    raise InvalidMapError(f"saveMap - Invalid tile state `{tile.get_state}` at {row, col} ")
                tempArr.append((tileStr,tile.get_terraform(),tile.get_mining()))
            saveArr.append(tempArr)

        # Save Array
        fileName = f"maps/{name}.awap23m"
        finJson = json.dumps(saveArr)
        with open(fileName, "w") as outfile:
            outfile.write(finJson)
        




