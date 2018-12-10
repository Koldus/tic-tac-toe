#!/usr/bin/env python
'''
Nao Playing Tic-Tac-To2, v0.1
Date: August 15, 2018
Company: DHL Information Services (Europe), s.r.o.

@author: Miroslav Koldus
'''

import sys, os
from naoqi import ALProxy

from nao_control import NaoControl
from nao_vision import NaoVision
from game_control import GameControl
from game_logging import GameLogger

from threading import Timer
import json

robotIp = "127.0.0.1"
port = 44469

live = True

robot = None
vision = None
game = None
logger = GameLogger()

def check_board_status():
    current_status = [0,1,2,3,4,5,6,7,8]
    last_status = [0,1,2,3,4,5,6,7,8]

    if game.board == current_status:
        logger.message("i", "No change in the board state")
        last_status = game.board
        t = Timer(2.0, check_board_status)
        t.start()
    else:
        if game.board == last_status:
            logger.message("i", "Board state change confirmed. Robot's turn.")
        else:
            logger.message("i", "Board state change identified, waiting for confirmation.")
            last_status = game.board
            t = Timer(2.0, check_board_status)
            t.start()        


def initialize_game(robotIP, port):
    # Setup robot connection + default position
    global robot
    robot = NaoControl(robotIP, port)
    robot.assume_initial_position()
    
    # Setup robot's vision connection + create proxy
    global vision
    
    vision = NaoVision(robotIP, port)
    if(live):
        vision.create_proxy()
    else:
        vision.connect_dev_camera()

    # Search for the board
    print("At this point, I should search for the board to confirm the physical setup")
    i = 0
    # while True:
    #     if( i<=10 ):
    #         break
    #     i += 1


    print(i)
    
    # Setup game controller
    global game
    game = GameControl()

    # -------------------------------
    #           Start the game
    # -------------------------------
    print("Ready to start the game")
    # check_board_status()

if __name__ == '__main__':
    # Initialize game configuration
    # robotIp = "192.168.8.101"
    # port = 9559 # Choregraphe tends to change ports on your local environment

    for arg in sys.argv:
        arg_b = arg.split(':')
        if arg_b[0] == "-dev":
            live = False
        if arg_b[0] == "-ip":
            robotIp = arg_b[1]
        if arg_b[0] == "-port":
            port = arg_b[1]

    try:
        logger.message("i", "Robot's IP address set to " + str(robotIp))
        logger.message("i", "Robot's port set to " + str(port))
        
        initialize_game(robotIp, port)
    except Exception as e:
        logger.message("e", "Game couldn't be started")
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno,e)