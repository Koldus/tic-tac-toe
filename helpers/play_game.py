from game_control import GameControl

import logging

logging.basicConfig(format = '%(asctime)s;%(levelname)s;%(filename)s;%(message)s', level = logging.DEBUG)

game = GameControl(logging)

# state = [ [0, 0, 0], [0, 0, 0], [0, 0, 0] ]
# depth = 9
# player = game.robot

# game.minimax(state, depth, player)

game.play()