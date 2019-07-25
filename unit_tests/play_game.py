from game_control import GameControl

import logging
logging.basicConfig(format = '%(asctime)s;%(levelname)s;%(filename)s;%(message)s', level = logging.DEBUG)

game = GameControl(logging)

print(game.evaluate_board([ [1, 0, 0], [0, 1, 0], [0, 0, 1] ]))
print(game.evaluate_board([ [-1, 0, 0], [0, -1, 0], [0, 0, -1] ]))
print(game.evaluate_board([ [1, -1, 1], [-1, -1, 1], [1, 1, -1] ]))
print(game.evaluate_board([ [1, 0, 0], [0, -1, 0], [0, 0, 1] ]))

print(game.play([ [1, 0, 0], [0, 1, 0], [0, 0, 1] ]))
print(game.play([ [-1, 0, 0], [0, -1, 0], [0, 0, -1] ]))
print(game.play([ [1, -1, 1], [-1, -1, 1], [1, 1, -1] ]))
print(game.play([ [1, 0, 0], [0, -1, 0], [0, 0, 1] ]))

# Start the test game ...

state = [ [0, 0, 0], [0, 0, 0], [0, 0, 0] ]
who_starts = raw_input('Who starts? (1) for robot and (0) for human ... ')

if int(who_starts) == 1:
    turn = 1
else:
    turn = -1

while True:

    if turn == 1:
        move = game.play(state)
        print(move)

        if move[2] == 1:
            print('robot wins, break')
            break
        elif move[2] == -1:
            print('you win, break')
            break
        elif move[2] == 0:
            print('its a tie')
            break
    else:
        game.render(state)
        position = raw_input('Where would you like to play? (raw colum) ')
        pos = position.split()
        move = [int(x) for x in pos]
    
    state[move[0]][move[1]] = turn
    turn = -turn

print('game over')