#!/usr/bin/env python
'''
Nao Playing Tic-Tac-Toe, v0.1
Date: June 18, 2019
Company: DHL Information Services (Europe), s.r.o.

@author: mkoldus
'''

import sys
import argparse
from threading import Timer
import logging

from config import *
from nao_control import NaoControl as NaoControlModule
from naoqi import ALBroker

# Default parameter
robotIp = "127.0.0.1"
port = 9559

NaoControl = None

# Setup the main logger
logging.basicConfig(filename = 'html/data/main.log', filemode = 'w', format = '%(asctime)s;%(levelname)s;%(filename)s;%(message)s', level = logging.DEBUG)

# def check_board_status():
#     current_status = [0,1,2,3,4,5,6,7,8]
#     last_status = [0,1,2,3,4,5,6,7,8]

#     if game.board == current_status:
#         logging.info("No change in the board state")
#         last_status = game.board
#         t = Timer(2.0, check_board_status)
#         t.start()
#     else:
#         if game.board == last_status:
#             logging.info("Board state change confirmed. Robot's turn.")
#             pass
#         else:
#             logging.info("Board state change identified, waiting for confirmation.")
#             last_status = game.board
#             t = Timer(2.0, check_board_status)
#             t.start()        


def initialize_game():
    
    # Setup robot connection
    global NaoControl
    NaoControl = NaoControlModule("NaoControl", logging)
    #NaoControl = robot

    if(not NaoControl.state.init_completed):
        logging.warning("%s initialization process couldn't be completed and the game ended.", str(xo_config_robot_name))
        logging.debug("init_completed state evaluated as False")
        sys.exit()

    # Initialize the game
    NaoControl.begin_game()

    if(not NaoControl.state.game_ready):
        logging.warning("The game initialization process couldn't be completed and the application hasended.")
        logging.debug("game_ready state evaluated as False")
        sys.exit()
    print("Jdu neskoncit")
    # Keep playing until the end
    while NaoControl.state.game_ready:
        NaoControl.state.next_placement = 4
        pass
    
    if( NaoControl.state.result == 0 ):
        logging.info("Game ended: Human won.")
    elif( NaoControl.state.result == 1 ):
        logging.info("Game ended: A tie.")
    elif( NaoControl.state.result == 2 ):
        logging.info("Game ended: Marvin won.")
    else:
        logging.error("Application ended correctly, but a correct result.")

    sys.exit()



## -------------------------------------------------------------
 #    START THE MAIN PROCESS
## -------------------------------------------------------------
if __name__ == '__main__':
    
    # Initialize game configuration based on input from command line
    parser = argparse.ArgumentParser()
    parser.add_argument('--ip', type=str, default="127.0.0.1", help="Robot's IP address")
    parser.add_argument('--port', type=int, default="9559", help="Robot's port number")

    args = parser.parse_args()

    robotIp = args.ip
    port = args.port

    try:
        logging.info("Robot's IP address set to %s", str(robotIp))
        logging.info("Robot's port set to %s", str(port))
        
        myBroker = ALBroker("myBroker",
            "0.0.0.0",   # listen to anyone
            0,           # find a free port and use it
            robotIp,     # parent broker IP
            port)        # parent broker port

        # Initiate the game
        initialize_game()
        
    except Exception as e:
        # Log the errors before game termination
        print(e)
        #logging.fatal("Game exectution failed")
        logging.debug('Error message: %s', str(e).replace("\n"," ").replace("\t"," "))
        
        global NaoControl
        if NaoControl != None:
            NaoControl.relax_left_arm()
            NaoControl.relax_right_arm()
