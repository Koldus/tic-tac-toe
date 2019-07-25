import numpy as np
from naoqi import ALProxy
from naoqi import ALModule
import almath
import cv2
import random
import functools
import time
import motion
import sys

import argparse
from naoqi import ALBroker
import logging

from config import *
# from nao_vision import NaoVision
# from game_control import GameControl

import inspect

memory = None

class State:
    init_completed = False
    board_visible = False
    game_ready = False
    board = [[0,0,0], [0,0,0], [0,0,0]]
    result = -1
    begging_left_arm = False
    begging_right_arm = False
    next_placement = -1
    def __init__(self):
        pass

class NaoControl(ALModule):    
    '''
    Main class that controls the game and all interaction with the Nao robot.
    '''
    
    SAY_TOKEN_GIVEN = ["Fine", "Thanks", "OK. I got it.", "Let me play"]


    ## -------------------------------------------------------------
    #    MAIN FUNCTIONS
    ## -------------------------------------------------------------

    def __init__(self, name, logging):        
        '''
        Constructor for NaoControl class - establishes necessary proxies with Nao robot and instantiates the game and vision objects.
        '''
        global NaoControl

        ALModule.__init__(self, name)

        self.logger = logging
        self.state = State()

        # Setup proxies to enable message exchange with the robot
        self.autoProxy = ALProxy("ALAutonomousLife")
        self.awarenessProxy = ALProxy("ALBasicAwareness")
        self.postureProxy = ALProxy("ALRobotPosture")
        self.motionProxy = ALProxy("ALMotion")
        self.cameraProxy = ALProxy("ALVideoDevice")
        self.ledProxy = ALProxy("ALLeds")
        self.tts = ALProxy("ALTextToSpeech")
        global memory
        memory = ALProxy("ALMemory")

        self.logger.debug("Proxies with %s established", str(xo_config_robot_name))

        # Configure camera
        # self.configure_camera()
        # im = self.take_a_look()
        
        # Initiate the CV module and game
        # self.vision = NaoVision((im[0], im[1]), logging)
        # self.game = GameControl(logging)

        # Assume the initial position and wait for the vision to be enabled
        self.assume_initial_position()

        # Confirm the initialization process has been concluded 
        # self.state.init_completed = True

        self.beg_for_token_start(False)
        self.prepare_for_placement(4)



    def arm_responsible(self, next_placement):
        #returns isLeft
        if next_placement[1] == 0:
            return True
        else:
            return False


    def assume_initial_position(self):
        '''
        Function that disables the autonomous life and lunches the sequence to assume the initial position.
        The sequence ends when all modules are identified and hands are safely relaxed on the table after the playboard has been identified. 
        '''
        
        ## Shutting down awareness
        self.autoProxy.setState("disabled")
        self.awarenessProxy.stopAwareness()
        self.motionProxy.stiffnessInterpolation("Body", 1.0, 1.0)

        self.logger.debug("Initial position initiated by disabling autonomous life and basic awareness. Body stiffness enabled.")

        
    def relax_left_arm(self):
        rNames = ["LShoulderPitch", "LShoulderRoll", "LElbowYaw", "LElbowRoll", "LWristYaw"]
        rValues = [rad(48.0), rad(1.0), rad(-85.0), rad(-48.0), rad(5.0)]
        rTimes = [2.0] * 5
        self.motionProxy.angleInterpolation(rNames, rValues, rTimes, True)
        self.motionProxy.setStiffnesses("LArm", 0.0)
        time.sleep(1.0)

    def relax_right_arm(self):
        rNames = ["RShoulderPitch", "RShoulderRoll", "RElbowYaw", "RElbowRoll", "RWristYaw"]
        rValues = [rad(48.0), rad(1.0), rad(85.0), rad(48.0), rad(5.0)]
        rTimes = [2.0] * 5
        self.motionProxy.angleInterpolation(rNames, rValues, rTimes, True)
        self.motionProxy.setStiffnesses("RArm", 0.0)
        time.sleep(1.0)

    def onTouched(self, strVarName, value):
        global memory
        memory.unsubscribeToEvent("TouchChanged", "NaoControl")

        for p in value:
            if p[1]:
                if p[0] == "RArm":
                    self.beg_for_token_finish(False)
                if p[0] == "LArm":
                    self.beg_for_token_finish(True)

    def beg_for_token_start(self, isLeftArm):
        self.logger.debug("Begging start. Left? {}".format(isLeftArm))
        if isLeftArm:
            # left arm
            self.motionProxy.setStiffnesses("LArm", 1.0)
            self.state.begging_left_arm = True
            self.state.begging_right_arm = False
            rNames = ["LShoulderPitch", "LShoulderRoll", "LElbowYaw", "LElbowRoll", "LWristYaw", "LHand"]
            rValues = [rad(-14.1),      rad(24.0),       rad(-77.9),  rad(-21.1),   rad(-104.5), 0.53]
        else:
            # right arm
            self.motionProxy.setStiffnesses("RArm", 1.0)
            self.state.begging_right_arm = True
            self.state.begging_left_arm = False
            rNames = ["RShoulderPitch", "RShoulderRoll", "RElbowYaw", "RElbowRoll", "RWristYaw", "RHand"]
            rValues = [rad(-14.1),      rad(-24.0),      rad(77.9),   rad(21.1),    rad(104.5),  0.53]

        rTimes = [2.0] * 6
        self.motionProxy.angleInterpolation(rNames, rValues, rTimes, True)
        # global memory
        # memory.subscribeToEvent("TouchChanged", "NaoControl", "onTouched")


    def beg_for_token_finish(self, isLeftArm):
        self.logger.debug("Begging finish. Left? {}".format(isLeftArm))
        if (isLeftArm == True and self.state.begging_left_arm == True) or (isLeftArm == False and self.state.begging_right_arm == True):
            self.state.begging_left_arm = False
            self.state.begging_left_arm = False
            self.tts.say(self.SAY_TOKEN_GIVEN[random.randrange(len(self.SAY_TOKEN_GIVEN))])
            self.prepare_for_placement(self.state.next_placement)

    def prepare_for_placement(self, placement):
        self.logger.debug("PREPARE to placing to {}".format(placement))
        if placement != -1:
            # TODO read from movement repository
            #rNames = ["RShoulderPitch", "RShoulderRoll", "RElbowYaw", "RElbowRoll", "RWristYaw"]
            #rValues = [rad(40.7),       rad(11.4),       rad(21.3),   rad(55.3),    rad(-34.4)]
            #rTimes = [2.0] * 5
            #self.motionProxy.angleInterpolation(rNames, rValues, rTimes, True)

            #prepare to move to placement position
            self.motionProxy.setStiffnesses("RArm", 1.0)
            self.state.begging_right_arm = True
            self.state.begging_left_arm = False
            rNames = ["RShoulderPitch", "RShoulderRoll", "RElbowYaw", "RElbowRoll", "RWristYaw", "RHand"]
            rValues = [rad(5.7),      rad(4.7),      rad(-16.4) ,     rad(63.1),    rad(9.6),  0.53]
            rTimes = [2.0] * 6
            self.motionProxy.angleInterpolation(rNames, rValues, rTimes, True)
            time.sleep(3.0)

            # Open hand
            self.motionProxy.setStiffnesses("RArm", 1.0)
            self.motionProxy.setAngles("RHand", 0.99, 0.1)
            time.sleep(2.0)
            self.motionProxy.setAngles("RHand", 0.1, 0.1)
            self.relax_right_arm()
        self.state.my_turn = False


        
def rad(val):
    return val * almath.TO_RAD




if __name__ == '__main__':
    # Initialize game configuration based on input from command line
    parser = argparse.ArgumentParser()
    parser.add_argument('--ip', type=str, default="127.0.0.1", help="Robot's IP address")
    parser.add_argument('--port', type=int, default="9559", help="Robot's port number")

    args = parser.parse_args()

    robotIp = args.ip
    port = args.port
    naoControl = None

    logging.basicConfig(format = '%(asctime)s;%(levelname)s;%(filename)s;%(message)s', level = logging.DEBUG)

    try:
        logging.info("Robot's IP address set to %s", str(robotIp))
        logging.info("Robot's port set to %s", str(port))
        
        myBroker = ALBroker("myBroker",
            "0.0.0.0",   # listen to anyone
            0,           # find a free port and use it
            robotIp,     # parent broker IP
            port)        # parent broker port

        # Initiate the game
        naoControl = NaoControl("NaoControl", logging)
        # initialize_game()
        
    except Exception as e:
        # Log the errors before game termination
        print(e)
        #logging.fatal("Game exectution failed")
        logging.debug('Error message: %s', str(e).replace("\n"," ").replace("\t"," "))
        
        if naoControl != None:
            naoControl.relax_left_arm()
            naoControl.relax_right_arm()
            naoControl.cameraProxy.unsubscribe(NaoControl.video_client)
