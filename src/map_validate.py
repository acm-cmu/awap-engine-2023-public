from src.game_constants import GameConstants
from pathlib import Path
import json
import traceback

def get_rot_sym( height, width):
    def rot_sym(r, c):
        return height - r - 1, width - c - 1
    return rot_sym
def get_hor_sym( height, width):
    def hor_sym(r, c):
        return height - r - 1, c
    return hor_sym
def get_ver_sym( height, width):
    def ver_sym(r, c):
        return r, width - c - 1
    return ver_sym

def val_map_wrap(map):
    try:
        validate_map("current", map)
    finally:
        # traceback.print_exc()
        print("\n\nMAP IS BAD SEE BELOW REASONS")
        print("MAKE SURE YOU HAVE THE LATEST MAPS FROM GITHUB")
        print("IF THIS MAP IS WHAT IS CURRENTLY ON GITHUB, PLEASE LET US KNOW ON DISCORD, THANK YOU!")
        print("\n")


    
def validate_map(map_name, map):
    assert type(map) == list, "map is not a list"
    assert len(map) > 0, "map is an empty list"

    height, width = len(map), len(map[0])

    # make sure each 
    for row in range(height):
        assert len(map[row]) == width, f"bad map {map_name} weird row {row}"

    sym_fs = [
        ("rot", get_rot_sym(height, width)), 
        ("hor", get_hor_sym(height, width)), 
        ("ver", get_ver_sym(height, width))
    ]

    has_sym = None

    all_bads = {}
    # validate symmetry
    for sname, sfunc in sym_fs:
        # print(sname, sfunc)

        bads = []

        # loop through map
        for row in range(height):
            for col in range(width):
                srow, scol = sfunc(row, col)

                cur_tile = map[row][col]
                sym_tile = map[srow][scol]

                if tuple(cur_tile) != tuple(sym_tile):
                    bads += [(row, col, srow, scol, cur_tile, sym_tile)]

        
        all_bads[sname] = bads

        if len(bads) > 0:
            has_sym = sname
    

    print("sym", has_sym)
    if has_sym is None:
        print(f"Bad map {map_name}")
        for sname, bads in all_bads.items():
            print("\t", sname, bads[0])




    # check that all mine tiles are > 0
    for row in range(height):
        for col in range(width):
            ttype, terr, mine = map[row][col]

            status = f"t:{terr} m:{mine}"

            if ttype == "I":
                assert terr == 0 and mine == 0, f"weird impass {status} at {row, col}"
            elif ttype == "T":
                assert mine == 0 and terr in [-5, 0, 5], f"weird terr {status} at {row, col}"
            elif ttype == "M":
                assert terr == 0 and GameConstants.MINING_MIN <= mine <= GameConstants.MINING_MAX, f"weird mine {status} at {row, col}"
            else:
                assert False, f"unknown tile state {ttype}"




def val_maps():
    map_folder = Path("./maps")
    files = list(map_folder.glob("*.awap23m"))
    # print(files)

    goods = []
    bads = []
    for p in files:
        fname = p.name
        print("Checking", fname)
        with open(p, "r") as f:
            obj = json.load(f)

            try:
                validate_map(fname, obj)
            except AssertionError:
                traceback.print_exc()
                print(f"bad map {fname}")
                bads += [fname]
            else:
                print(f"good map {fname}")
                goods += [fname]

            print("\n\n")
            # print(str(obj)[:50])
    
    print("Goods:", goods)
    print("Bads:", bads)