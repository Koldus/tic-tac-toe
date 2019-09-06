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
from flask import Flask, send_from_directory, request, Response
import json
from config import *
from nao_control import NaoControl
from naoqi import ALBroker
import traceback
OK = 'ok'

# Default parameter
robotIp = "marvin.local"
port = 9559
nao_control = None

def sigint_handler(signum, frame):
    shutdown_robot()

def shutdown_robot():
    print("Shutting down. Good night.")
    if nao_control != None:
        nao_control.relax_arms()
        nao_control.cameraProxy.unsubscribe(nao_control.video_client)
    sys.exit()

def initialize_game():
    
    # Setup robot connection
    global nao_control
    nao_control = NaoControl("nao_control", logging)

    if(not nao_control.state.init_completed):
        logging.warning("%s initialization process couldn't be completed and the game ended.", str(xo_config_robot_name))
        logging.debug("init_completed state evaluated as False")
        shutdown_robot()

## -------------------------------------------------------------
 #    START THE MAIN PROCESS
## -------------------------------------------------------------

# Initialize game configuration based on input from command line
parser = argparse.ArgumentParser()
parser.add_argument('--ip', type=str, default=robotIp, help="Robot's IP address")
parser.add_argument('--port', type=int, default=port, help="Robot's port number")
args = parser.parse_args()
robotIp = args.ip
port = args.port

logging.basicConfig(filename = 'static/data/main.log', filemode = 'w', format = '%(asctime)s;%(levelname)s;%(filename)s;%(message)s', level = logging.DEBUG)
signal.signal(signal.SIGINT, sigint_handler)

try:
    logging.info("Robot's IP address set to %s", str(robotIp))
    logging.info("Robot's port set to %s", str(port))
    
    myBroker = ALBroker("myBroker",
        "0.0.0.0",   # listen to anyone
        0,           # find a free port and use it
        robotIp,     # parent broker IP
        port)        # parent broker port

    initialize_game()
    
    # Start webserver
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.WARN)
    print("Flask to be approached")
    app = Flask(__name__)  # wait for requests

    ## -------------------------------------------------------------
    #    API ROUTES
    ## -------------------------------------------------------------
    @app.route('/')
    def static_index():
        return send_from_directory('static', 'index.html')

    @app.route('/<path:filename>')
    def static_resources(filename):
        return send_from_directory('static', filename)

    @app.route('/api/start_game')
    def api_start_game():
        nao_control.begin_game()
        return OK, 200

    @app.route('/api/stop_game')
    def api_stop_game():
        nao_control.stop_game()
        return OK, 200

    @app.route('/api/get_state')
    def api_get_status():
        global nao_control
        r = Response(json.dumps(nao_control.state.convert_to_dict()), mimetype='application/json')
        print(r)
        return r

    @app.route('/api/say')
    def api_say():
        global nao_control
        try:
            text = str(request.args.get('text'))
            if nao_control != None:
                nao_control.tts_say([text])
                return OK, 200
            else:
                return 'Not connected', 506
        except Exception as e:
            logging.Error(e)
            return 'Error', 507


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


    app.run()
    print("Passed the Flask")
    nao_control.begin_game()
        
except Exception as e:
    print(e)
    traceback.print_exc(file=sys.stdout)
    logging.debug('Error message: %s', str(e).replace("\n"," ").replace("\t"," "))
    shutdown_robot()



