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

def initialize_game():
    
    # Setup robot connection
    global NaoControl
    NaoControl = NaoControlModule("NaoControl", logging)
    #NaoControl = robot

    if(not NaoControl.state.init_completed):
        logging.warning("%s initialization process couldn't be completed and the game ended.", str(xo_config_robot_name))
        logging.debug("init_completed state evaluated as False")
        sys.exit()

    # Play the game
    NaoControl.begin_game()

    # Unsubscribe from the camera feed
    NaoControl.cameraProxy.unsubscribe(NaoControl.video_client)


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
            NaoControl.relax_arms()
            NaoControl.cameraProxy.unsubscribe(NaoControl.video_client)
