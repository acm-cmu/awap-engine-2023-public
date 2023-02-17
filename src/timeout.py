import multiprocessing

if __name__ == "__main__":
    p = multiprocessing.Process(target=player.play_turn, name="run_player")
    p.start()
    p.join(GameConstants.TIME_LIMIT)
    if p.is_alive():
        p.terminate()
    raise ValueError