#!/usr/bin/env python
'''
Nao Playing Tic-Tac-Toe, v0.1
Date: June 18, 2019
Company: DHL Information Services (Europe), s.r.o.

@author: mkoldus
'''

import sys, os
import argparse
from threading import Timer
import logging
from flask import Flask
from flask import send_from_directory, request
import json

from config import *

# Default parameter
robotIp = "127.0.0.1"
port = 9559

NaoControl = None

# Setup the main logger
logging.basicConfig(filename = 'static/data/main.log', filemode = 'w', format = '%(asctime)s;%(levelname)s;%(filename)s;%(message)s', level = logging.DEBUG)

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
#if __name__ == '__main__':
    
# Start webserver
#app = Flask(__name__, static_url_path='/html')
app = Flask(__name__)



## -------------------------------------------------------------
#    API ROUTES
## -------------------------------------------------------------

@app.route('/api/connect')
def api_connect():
    print('connecting')
    # Initiate the game
    try:
        print('connecting')
        robotIp = request.args.get('ip')
        port = request.args.get('port')
        logging.info("Connecting to robot at %s:%d", str(robotIp), int(port))
        
        myBroker = ALBroker("myBroker",
            "0.0.0.0",   # listen to anyone
            0,           # find a free port and use it
            robotIp,     # parent broker IP
            port)        # parent broker port

        from nao_control import NaoControl as NaoControlModule
        from naoqi import ALBroker
        initialize_game()

        return 'ok'
    except Exception as e:
        logging.error('Error message: %s', str(e).replace("\n"," ").replace("\t"," "))
        if NaoControl != None:
            NaoControl.relax_arms()
            NaoControl.cameraProxy.unsubscribe(NaoControl.video_client)
        return e


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


