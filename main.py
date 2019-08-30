#!/usr/bin/env python
'''
Nao Playing Tic-Tac-Toe, v0.1
Date: June 18, 2019
Company: DHL Information Services (Europe), s.r.o.

@author: mkoldus, jslesing
'''
import sys, os, signal
import argparse
from threading import Timer
import logging
from flask import Flask, send_from_directory, request
import json
from config import *
from nao_control import NaoControl as NaoControlModule

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

def initialize_robot():
    global NaoControl
    NaoControl = NaoControlModule("NaoControl", logging)

    if(not NaoControl.state.init_completed):
        logging.warning("%s initialization process couldn't be completed and the game ended.", str(xo_config_robot_name))
        logging.debug("init_completed state evaluated as False")
        sys.exit()

## -------------------------------------------------------------
 #    START THE MAIN PROCESS
## -------------------------------------------------------------
#if __name__ == '__main__':
    
signal.signal(signal.SIGINT, sigint_handler)

# Setup the main logger
logging.basicConfig(filename = 'static/data/main.log', filemode = 'w', format = '%(asctime)s;%(levelname)s;%(filename)s;%(message)s', level = logging.DEBUG)

# Connect and wake up the robot
try:
    logging.info("Connecting to robot at %s:%d", str(robotIp), int(port))
    
    from naoqi import ALBroker
    myBroker = ALBroker("myBroker",
        "0.0.0.0",        # listen to anyone
        0,                # find a free port and use it
        str(robotIp),     # parent broker IP
        int(port))        # parent broker port
    initialize_robot()
    NaoControl.begin_game()  # TODO start from API
except Exception as e:
    logging.error('Error message: %s', str(e).replace("\n"," ").replace("\t"," "))
    shutdown_robot()
    sys.exit()

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

