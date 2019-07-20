import numpy as np
from naoqi import ALProxy
from naoqi import ALModule
import almath
import cv2
import random
import functools
import time

from config import *
from nao_vision import NaoVision
from game_control import GameControl

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
        Constructor for NaoControl class, takes ip_address, port and name for comms with the Nao robot and a logger object.
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
        self.configure_camera()
        im = self.take_a_look()
        
        # Initiate the CV module and game
        self.vision = NaoVision((im[0], im[1]), logging)
        self.game = GameControl(logging)

        # Assume the initial position and wait for the vision to be enabled
        self.assume_initial_position()

        # Confirm the initialization process has been concluded 
        self.state.init_completed = True

    def is_board_changed(self, board_seen):
        print(board_seen)
        print(self.state.board)
        for row in range (0,2):
            for col in range (0,2):
                if board_seen[row][col] != self.state.board[row][col]:
                    self.logger.debug("Compare board [{},{}] old:{} seen:{}".format(row, col, self.state.board[row][col], board_seen[row][col]))
                    return True
        return False


    def wait_for_my_turn_completion(self):
        while self.state.my_turn:
            time.sleep(0.1)


    def arm_responsible(self, next_placement):
        #returns isLeft
        if next_placement[1] == 0:
            return True
        else:
            return False

    def is_game_finished(self, wins):
        if wins == -1:
            self.game_lost()
            return True
        elif wins == 1:
            self.game_won()
            return True
        elif wins == 0:
            self.game_tie()
            return True
        return False

    def game_lost(self):
        self.tts.say("Hmmm. I lost. I am sure I will win next time.")

    def game_won(self):
        self.tts.say("Yupee. Of course, I won. I always win.")
    
    def game_tie(self):
        self.tts.say("Good play. Your moves were optimal.")

    def wait_for_opponent_token(self):
        while True:
            picture = self.take_a_look()
            board_seen = self.vision.get_current_state(picture)
            self.logger.debug("board_seen {}".format(board_seen))
            if self.is_board_changed(board_seen):
                self.state.my_turn = True
                return board_seen
            else:
                time.sleep(0.5)


    def begin_game(self):
        self.logger.debug("Game begins")
        self.state.game_ready = True
        self.tts.say("Lets start the game")

        while True:
            board_seen = self.wait_for_opponent_token()
            self.tts.say("Nice play")
            self.state.next_placement = self.game.play(board_seen)
            if self.is_game_finished(self.state.next_placement[2]):
                break
            self.beg_for_token_start(self.arm_responsible(self.state.next_placement))
            self.wait_for_my_turn_completion()
            self.tts.say("Your turn my dear")

        self.tts.say("Do you want to play again? I am finished.")

    
    ## -------------------------------------------------------------
    #    SUPPORTING FUNCTIONS
    ## -------------------------------------------------------------

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

        # Setup the body posture with you
        if( self.postureProxy.getPosture() != xo_config_base_position ):
            id = self.postureProxy.goToPosture(xo_config_base_position, 1.0)
            self.postureProxy.wait(id, 0)


        # Configure head to the right position
        self.motionProxy.setStiffnesses("Head", 1.0)
        hNames = ["HeadPitch", "HeadYaw"]
        hValues = [(29 * almath.TO_RAD), (0.0 * almath.TO_RAD)]
        hTimes = [2.0] * 2
        self.motionProxy.angleInterpolation(hNames, hValues, hTimes, True)

        time.sleep(1.0)

        # Configure arms to the right position
        rNames = ["RShoulderPitch", "RShoulderRoll", "RElbowYaw", "RElbowRoll", "RWristYaw", "LShoulderPitch", "LShoulderRoll", "LElbowYaw", "LElbowRoll", "LWristYaw"]
        rValues = [rad(10.3), rad(-0.3), rad(9.5), rad(2.5), rad(5.0),
                   rad(10.3), rad(-0.3), rad(9.5), rad(2.5), rad(5.0)]
        rTimes = [2.0] * 10
        self.motionProxy.angleInterpolation(rNames, rValues, rTimes, True)
        self.ledProxy.randomEyes(1.0)
        self.ledProxy.off("FaceLeds")

        # Wait until a board has been identified and complete the relaxed position
        self.tts.say("Dear lord, I need a board.")
        while not self.vision.find_board( self.take_a_look() ):
            pass
        self.ledProxy.randomEyes(1.0)
        self.ledProxy.off("FaceLeds")
        self.tts.say("I got it.")

        # Put the hands down and relax
        self.relax_left_arm()
        self.relax_right_arm()

        # Close the initialization process
        self.logger.debug("Initial position assumed, default position set to " + xo_config_base_position + " for efficient stability")


        
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
        self.motionProxy.setStiffnesses("RArm", 1.0)
        self.motionProxy.setStiffnesses("LArm", 1.0)
        if isLeftArm:
            # left arm
            self.state.begging_left_arm = True
            self.state.begging_right_arm = False
            rNames = ["LShoulderPitch", "LShoulderRoll", "LElbowYaw", "LElbowRoll", "LWristYaw", "LHand"]
            rValues = [rad(-14.1),      rad(24.0),       rad(-77.9),  rad(-21.1),   rad(-104.5), 0.53]
        else:
            # right arm
            self.state.begging_right_arm = True
            self.state.begging_left_arm = False
            rNames = ["RShoulderPitch", "RShoulderRoll", "RElbowYaw", "RElbowRoll", "RWristYaw", "RHand"]
            rValues = [rad(-14.1),      rad(-24.0),      rad(77.9),   rad(21.1),    rad(104.5),  0.53]

        rTimes = [2.0] * 6
        self.motionProxy.angleInterpolation(rNames, rValues, rTimes, True)
        global memory
        memory.subscribeToEvent("TouchChanged", "NaoControl", "onTouched")


    def beg_for_token_finish(self, isLeftArm):
        self.logger.debug("Begging finish. Left? {}".format(isLeftArm))
        if (isLeftArm == True and self.state.begging_left_arm == True) or (isLeftArm == False and self.state.begging_right_arm == True):
            self.state.begging_left_arm = False
            self.state.begging_left_arm = False
            self.tts.say(self.SAY_TOKEN_GIVEN[random.randrange(len(self.SAY_TOKEN_GIVEN))])
            self.prepare_for_placement(self.state.next_placement)

    def prepare_for_placement(self, placement):
        print("PREPARE")
        print(placement)
        if self.state.next_placement != -1:
            rNames = ["RShoulderPitch", "RShoulderRoll", "RElbowYaw", "RElbowRoll", "RWristYaw"]
            # TODO read from movement repository
            rValues = [rad(40.7),       rad(11.4),       rad(21.3),   rad(55.3),    rad(-34.4)]
            rTimes = [2.0] * 5
            self.motionProxy.angleInterpolation(rNames, rValues, rTimes, True)
            time.sleep(1.0)

            # Open hand
            self.motionProxy.setStiffnesses("RArm", 1.0)
            self.motionProxy.setAngles("RHand", 0.99, 0.1)
            time.sleep(2.0)
            self.motionProxy.setAngles("RHand", 0.1, 0.1)
            self.relax_right_arm()
        self.state.my_turn = False


    def configure_camera(self):
        '''
        configure_camera method is used to setup the camera proxy and camera matrix
        '''
        
        # Setup camera proxy to be used for image retrievals for later processing
        self.cameraProxy.setActiveCamera(xo_config_camera_id)

        self.logger.debug("Connection with camera established")
        
        # Camera Matrix will later be used for solvePnP algorithm
        self.cameraMatrix = np.zeros((3,3), dtype=np.float64)
        self.cameraMatrix[0][0] = xo_config_intrinsic_parameters[0] ## fx
        self.cameraMatrix[1][1] = xo_config_intrinsic_parameters[1] ## fy
        self.cameraMatrix[0][2] = xo_config_intrinsic_parameters[2] ## cx
        self.cameraMatrix[1][2] = xo_config_intrinsic_parameters[3] ## cy
        self.cameraMatrix[0][1] = xo_config_intrinsic_parameters[4] ## s
        self.cameraMatrix[2][2] = 1.0

        self.logger.debug("Camera Matrix for SolvePnP established: %s", str(self.cameraMatrix.tolist()))

    
    def take_a_look(self):
        video_client = self.cameraProxy.subscribe("python_client", 3, 11, 5)
        nao_image = self.cameraProxy.getImageRemote(video_client)
        self.cameraProxy.unsubscribe(video_client)

        self.logger.debug("A camera snapshot was taken")
        return nao_image


    def find_target_position(self, section_id):
        print("Calculate target position")
        pass


    def select_hand(self, target_position):
        print("Choose active hand based on the target position")
        pass


    def forward_kinematics(self, active_hand):
        print("Calculate joint position - Forward Kinematics")
        pass


    def inverse_kinematics(self, target_position):
        print("Calculate kinematic chain of target position - Inverse Kinematics")
        pass


    def make_move(self, section_id):
        target_position = self.find_target_position(section_id)
        active_hand = self.select_hand(target_position)
        print("Request token / pick up the token")
        joint_position = self.forward_kinematics(active_hand)
        joint_target = self.inverse_kinematics(target_position)
        print("Execute the move")
        pass
        
def rad(val):
    return val * almath.TO_RAD