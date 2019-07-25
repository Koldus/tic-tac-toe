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

        for r in range(3):
            for c in range(3):
                placement = [r,c, False]
                effector_side = self.arm_responsible(placement)
                self.beg_for_token_start(effector_side)

                self.motionProxy.setAngles(effector_side + "Hand", 0.45, 0.1)
                time.sleep(2.0)

                self.prepare_for_placement(placement)



    def arm_responsible(self, next_placement):
        if next_placement[1] == 0:
            return "L"
        else:
            return "R"


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

        
    def relax_arm(self, arm_side):
        rNames = [arm_side + "ShoulderPitch", arm_side + "ShoulderRoll", arm_side + "ElbowYaw", arm_side + "ElbowRoll", arm_side + "WristYaw"]
        if arm_side == "R":
            rValues = [rad(50.0), rad(-4.0), rad( 85.0), rad( 48.0), rad(5.0)]
        else:
            rValues = [rad(50.0), rad(10.0), rad(-85.0), rad(-48.0), rad(5.0)]
        rTimes = [2.0] * 5
        self.motionProxy.angleInterpolation(rNames, rValues, rTimes, True)
        self.motionProxy.setStiffnesses(arm_side + "Arm", 0.0)
        time.sleep(1.0)

    def onTouched(self, strVarName, value):
        # global memory
        # memory.unsubscribeToEvent("TouchChanged", "NaoControl")

        for p in value:
            if p[1]:
                if p[0] == "RArm":
                    self.beg_for_token_finish(False)
                if p[0] == "LArm":
                    self.beg_for_token_finish(True)

    def beg_for_token_start(self, arm_side):
        self.logger.debug("Begging start. Arm:{}".format(arm_side))
        if arm_side == "L":
            # left arm
            self.motionProxy.setStiffnesses("LArm", 1.0)
            self.state.begging_left_arm = True
            self.state.begging_right_arm = False
            rNames = ["LShoulderPitch", "LShoulderRoll", "LElbowYaw", "LElbowRoll", "LWristYaw", "LHand"]
            rValues = [rad(-14.1),      rad(24.0),       rad(-77.9),  rad(-21.1),   rad(-104.5), 0.51]
        else:
            # right arm
            self.motionProxy.setStiffnesses("RArm", 1.0)
            self.state.begging_right_arm = True
            self.state.begging_left_arm = False
            rNames = ["RShoulderPitch", "RShoulderRoll", "RElbowYaw", "RElbowRoll", "RWristYaw", "RHand"]
            rValues = [rad(-14.1),      rad(-24.0),      rad(77.9),   rad(21.1),    rad(104.5),  0.58]

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
        p_row = placement[0]
        p_col = placement[1]
        self.logger.debug("PREPARE to placing to {}".format(placement))
        if placement != -1:
            # TODO read from movement repository
            #rNames = ["RShoulderPitch", "RShoulderRoll", "RElbowYaw", "RElbowRoll", "RWristYaw"]
            #rValues = [rad(40.7),       rad(11.4),       rad(21.3),   rad(55.3),    rad(-34.4)]
            #rTimes = [2.0] * 5
            #self.motionProxy.angleInterpolation(rNames, rValues, rTimes, True)

            #x:forward, y:left
            rows = [0.05, 0, -0.05]
            cols = [0, 0.02, -0.03]

            #prepare to move to placement position
            effector_side = self.arm_responsible(placement)
            effector   = effector_side + "Arm"
            self.motionProxy.setStiffnesses(effector, 1.0)
            self.state.begging_right_arm = True
            self.state.begging_left_arm = False
            rNames = [effector_side + "ShoulderPitch", effector_side + "ShoulderRoll", effector_side + "ElbowYaw", effector_side + "ElbowRoll", effector_side + "WristYaw"]
            if effector_side == "R":
                rValues = [rad(5.7),      rad(4.7),      rad(-16.4) ,     rad(63.1),    rad(9.6)]
            else:
                rValues = [rad(6.3),      rad(9.9),      rad(-48.9) ,     rad(-31.6),    rad(4.1)]
            rTimes = [2.0] * 5
            self.motionProxy.angleInterpolation(rNames, rValues, rTimes, True)
            time.sleep(1.0)
            path = []
            frame      = motion.FRAME_TORSO
            axisMask   = almath.AXIS_MASK_VEL # just control position
            useSensorValues = False
            currentTf = self.motionProxy.getTransform(effector, frame, useSensorValues)
            targetTf  = almath.Transform(currentTf)
            print(rows[p_row], cols[p_col])
            targetTf.r1_c4 +=  rows[p_row] #x
            targetTf.r2_c4 +=  cols[p_col] #y
            path.append(list(targetTf.toVector()))
            targetTf.r3_c4 +=  -0.03 #z
            path.append(list(targetTf.toVector()))
            times      = [2.0, 2.5] # seconds
            self.motionProxy.transformInterpolations(effector, frame, path, axisMask, times)

            # Open hand
            self.motionProxy.setStiffnesses(effector, 1.0)
            self.motionProxy.setAngles(effector_side + "Hand", 0.89, 0.1)
            time.sleep(1.0)

            # Move up
            path = []
            targetTf.r3_c4 +=  0.03 #z
            path.append(list(targetTf.toVector()))
            times      = [0.5] # seconds
            self.motionProxy.transformInterpolations(effector, frame, path, axisMask, times)

            # Close hand
            self.motionProxy.setAngles(effector_side + "Hand", 0.1, 0.1)
            self.relax_arm(effector_side)
            time.sleep(1.0)
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
