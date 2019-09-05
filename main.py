#!/usr/bin/env python
'''
Nao Playing Tic-Tac-Toe, v0.2
Date: June 18, 2019
Company: DHL Information Services (Europe), s.r.o.

@author: mkoldus, jslesing
'''

import sys, signal
import argparse
from threading import Timer
import logging
from flask import Flask, send_from_directory, request
from config import *
from nao_control import NaoControl as NaoControlModule
from naoqi import ALBroker

# Default parameter
robotIp = "marvin.local"
port = 9559
NaoControl = None

def sigint_handler(signum, frame):
    shutdown_robot()

def shutdown_robot():
    print("Shutting down. Good night.")
    if NaoControl != None:
        NaoControl.relax_arms()
        NaoControl.cameraProxy.unsubscribe(NaoControl.video_client)

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
logging.basicConfig(filename = 'html/data/main.log', filemode = 'w', format = '%(asctime)s;%(levelname)s;%(filename)s;%(message)s', level = logging.DEBUG)

signal.signal(signal.SIGINT, sigint_handler)

if __name__ == '__main__':


    # Initialize game configuration based on input from command line
    parser = argparse.ArgumentParser()
    parser.add_argument('--ip', type=str, default=robotIp, help="Robot's IP address")
    parser.add_argument('--port', type=int, default=port, help="Robot's port number")

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
        
        if NaoControl != None:
            NaoControl.relax_arms()
            NaoControl.cameraProxy.unsubscribe(NaoControl.video_client)



# Start webserver
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)
app = Flask(__name__)

## -------------------------------------------------------------
#    API ROUTES
## -------------------------------------------------------------
@app.route('/')
def static_index():
    return send_from_directory('static', 'index.html')

@app.route('/<path:filename>')
def static_resources(filename):
    return send_from_directory('static', filename)

@app.route('/api/get_state')
def api_get_status():
    global NaoControl
    return flask.Response(json.dumps(NaoControl), mimetype='application/json')

@app.route('/api/say')
def api_say():
    global NaoControl
    try:
        text = request.args.get('text')
        if NaoControl != None:
            NaoControl.tts_say(text)
        else:
            return 'Not connected', 506
    except Exception as e:
        print(e)

@app.route('/api/get_img_camera')
def api_get_img_camera():
    try:
        return flask.Response('', mimetype='image/jpeg')
    except Exception as e:
        print(e)
        return 'chyba', 599

@app.route('/api/get_img_blob')
def api_get_img_blob():
    try:
        return flask.Response('', mimetype='image/jpeg')
    except Exception as e:
        print(e)
        return 'chyba', 599

@app.route('/api/get_img_rectified')
def api_get_img_rectified():
    try:
        return flask.Response('', mimetype='image/jpeg')
    except Exception as e:
        print(e)
        return 'chyba', 599

@app.route('/api/get_img_boardstate')
def api_get_img_boardstate():
    try:
        return flask.Response('', mimetype='image/jpeg')
    except Exception as e:
        print(e)
        return 'chyba', 599
