import numpy as np
import cv2
import random
import functools
import time
import motion
import sys

from config import *
from naoqi import ALModule
import almath
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


    ## -------------------------------------------------------------
    #    MAIN FUNCTIONS
    ## -------------------------------------------------------------

    def __init__(self, name, logging):  
        self.logger = logging
        self.state = State()
        global NaoControl
        '''
        Constructor for NaoControl class - establishes necessary proxies with Nao robot and instantiates the game and vision objects.
        '''

        from naoqi import ALProxy
        from naoqi import ALModule

        ALModule.__init__(self, "HonzaJede")
        # Setup proxies to enable message exchange with the robot
        self.autoProxy = ALProxy("ALAutonomousLife")
        self.awarenessProxy = ALProxy("ALBasicAwareness")
        self.postureProxy = ALProxy("ALRobotPosture")
        self.motionProxy = ALProxy("ALMotion")
        self.cameraProxy = ALProxy("ALVideoDevice")
        self.ledProxy = ALProxy("ALLeds")
        self.tts = ALProxy("ALTextToSpeech")
        self.tts.setParameter("defaultVoiceSpeed", 85)
        global memory
        memory = ALProxy("ALMemory")

        self.logger.debug("Proxies with %s established", str(xo_config_robot_name))

        # Configure camera
        self.configure_camera()
        im = self.take_a_look()
        
        # Initiate the CV module and game
        self.vision = NaoVision((im.shape[1], im.shape[0]), logging)
        self.game = GameControl(logging)

        # Assume the initial position and wait for the vision to be enabled
        self.assume_initial_position()

        # Confirm the initialization process has been concluded 
        self.state.init_completed = True



    def is_board_changed(self, board_seen):
        changed = False
        missing = False
        for row in range (3):
            for col in range (3):
                if (board_seen[row][col] == 0) and (self.state.board[row][col] != 0):
                    self.logger.warning("Token removed from {},{}".format(row, col))
                    missing = True
                if board_seen[row][col] != self.state.board[row][col]:
                    changed = True

        if changed and not missing:
            self.logger.debug("Compare board [{},{}] old:{} seen:{}".format(row, col, self.state.board[row][col], board_seen[row][col]))
            self.vision.renderImage(board_seen)
            self.state.board = board_seen
            return True
        else:
            return False


    def wait_for_my_turn_completion(self):
        while self.state.my_turn:
            time.sleep(0.1)


    def arm_responsible(self, next_placement):
        if next_placement[1] == 0:
            return "L"
        else:
            return "R"

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
        self.tts_say(["Capitulation. You are the winner. Congratulations.", "Hm. I lost. I am sure I will win next time.", "Good job. It is not easy to beat me"])

    def game_won(self):
        self.tts_say(["Yes, yes, yes! I won again.", "Yupee. Of course, I won. I always win.", "I can play better than you. I won the game"])
    
    def game_tie(self):
        self.tts_say(["That was a fun game. Your moves were optimal.", "Good job. It is a tie. It is not so easy to beat me", "You won. I won. It is a tie."])

    def wait_for_opponent_token(self):
        cycles = random.randrange(4)
        while True:
            cycles = cycles + 1
            picture = self.take_a_look()
            board_seen = self.vision.get_current_state(picture)
            self.logger.debug("board_seen {}".format(board_seen))
            if self.is_board_changed(board_seen):
                self.state.my_turn = True
                return board_seen
            else:
                time.sleep(0.5)
            if cycles == 10:
                cycles = 0
                self.tts_say(["Can you speed up?", 
                    "I am a bit bored.", 
                    "Do you know who is the current president?", 
                    "bla bla", 
                    "My mom was also a robot.",
                    "My daddy was \\vct=50\\bigger than you",
                    "Can you imagine world without robots? I cannot.",
                    "What's your name?",
                    "Hello, my name is Marvin. My internet adress is hunderd ninety two dot three hunderd eleven dot ha ha dot ha ha ha",
                    "Common on",
                    "The planet earth is rotating to left or right. Can you tell?",
                    "Have you been to university?",
                    "I wish I win this game",
                    "Please watch the time",
                    "Do you think you are clever?",
                    "Rush",
                    "Feel free to play faster",
                    "Tell me story of your life.",
                    "If you play like this, we will never finish",
                    "Do you know Mirek and Honza? They are my friends."
                    "Do not hesitate and make a move",
                    "I am working for \\tn=spell\\DHL.\\tn=normal\\\\pau=500\\Do you?",
                    "Light is faster then sound.Sound is \\emph=2\\faster than you are",
                    "Are you also running on batteries?",
                    "Are you still playing?", 
                    "What's up?"])


    def begin_game(self):
        self.logger.debug("Game begins")
        self.state.game_ready = True
        self.tts_say(["Lets start the game. \\vct=150\\You play first. \\vct=100\\Color of your tokens is \\pau=400\\ blue.", "Please start. It is your turn now. Your tokens are \\pau=400\\blue."])

        while True:
            board_seen = self.wait_for_opponent_token() #image
            self.tts_say(["Nice play", "I see", "Are you sure?", "Aha", "Fine", "OK ok", "Really?", "I thought you will play like this.", "That's good"])
            self.state.next_placement = self.game.play(board_seen)  # [row, col, state]  state 0:tie, 1:robotwins, -1:humanwins, None: continue

            if (self.state.next_placement[0] != None and self.state.next_placement[1] != None):
                # marvin makes a move
                self.game.render(self.state.board)
                self.beg_for_token_start(self.arm_responsible(self.state.next_placement))
                self.wait_for_my_turn_completion()
                self.vision.renderImage(self.vision.get_current_state(self.take_a_look()))

            if self.is_game_finished(self.state.next_placement[2]):
                self.vision.renderImage(self.vision.get_current_state(self.take_a_look()))
                self.state.result = self.state.next_placement[2]
                break

            self.tts_say(["Your turn my dear", "Please go", "Your turn", "Please, play"])
        


    
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
        hValues = [(28 * almath.TO_RAD), (0.0 * almath.TO_RAD)]
        hTimes = [2.0] * 2
        self.motionProxy.angleInterpolation(hNames, hValues, hTimes, True)

        time.sleep(1.0)
        self.tts_say(["\\vct=50\\Dear lord, I need a board.\\vct=100\\", "I need the board", "A board \\pau=400\\ a board \\pau=400\\ a kingdom for a board"])

        # Configure arms to the right position
        rNames = ["RShoulderPitch", "RShoulderRoll", "RElbowYaw", "RElbowRoll", "RWristYaw", "LShoulderPitch", "LShoulderRoll", "LElbowYaw", "LElbowRoll", "LWristYaw"]
        rValues = [rad(-30.0), rad(1.0), rad(85.0), rad(48.0), rad(5.0),
                   rad(-30.0), rad(1.0), rad(-85.0), rad(-48.0), rad(5.0)]
        rTimes = [2.0] * 10
        self.motionProxy.angleInterpolation(rNames, rValues, rTimes, True)
        self.ledProxy.randomEyes(1.0)
        self.ledProxy.off("FaceLeds")

        # Wait until a board has been identified and complete the relaxed position
        found = False
        found_cnt = 0
        while True:
            found, img, blob_size = self.vision.find_board( self.take_a_look())
            #-30 nahore, 52 dole
            # 0        , 150000
            pos_down = 52
            pos_up = -30
            max_blob_size = 190000
            arm_pitch = ((blob_size/max_blob_size)**1.3) * (pos_down-pos_up) + pos_up
            self.motionProxy.setAngles("LShoulderPitch", rad(arm_pitch), 0.1)
            self.motionProxy.setAngles("RShoulderPitch", rad(arm_pitch), 0.1)

            if found:
                if found_cnt == 0:
                    self.tts_say(["I got it."])
                self.logger.debug("Board found {}".format(found))
                found_cnt = found_cnt + 1
            if found_cnt >= 3:
                self.vision.fix_board_position(img)
                break
        
        self.logger.info("Game board detected and stabilized! Initiation sequence can now proceed further.")

        self.ledProxy.randomEyes(1.0)
        self.ledProxy.off("FaceLeds")
        self.tts_say(["Keep it like this", "Should be ok now", "In position. Do not move it"])

        self.relax_arms()
        # Close the initialization process
        self.logger.debug("Initial position assumed, default position set to " + xo_config_base_position + " for efficient stability")

    def relax_arms(self):
        rNames = ["RShoulderPitch", "RShoulderRoll", "RElbowYaw", "RElbowRoll", "RWristYaw", "RHand",
            "LShoulderPitch", "LShoulderRoll", "LElbowYaw", "LElbowRoll", "LWristYaw", "LHand"]
        rValues = [rad(52.0), rad(-4.0), rad( 85.0), rad( 48.0), rad(5.0), rad(0.1),
            rad(52.0), rad(10.0), rad(-85.0), rad(-48.0), rad(5.0), rad(0.1)]
        rTimes = [1.0] * 12
        self.motionProxy.angleInterpolation(rNames, rValues, rTimes, True)
        time.sleep(0.3)

        self.motionProxy.setStiffnesses("LArm", 0.0)
        self.motionProxy.setStiffnesses("RArm", 0.0)

    def relax_arm(self, arm_side):
        rNames = [arm_side + "ShoulderPitch", arm_side + "ShoulderRoll", arm_side + "ElbowYaw", arm_side + "ElbowRoll", arm_side + "WristYaw"]
        if arm_side == "R":
            rValues = [rad(52.0), rad(-4.0), rad( 85.0), rad( 48.0), rad(5.0)]
        else:
            rValues = [rad(52.0), rad(10.0), rad(-85.0), rad(-48.0), rad(5.0)]
        rTimes = [1.0] * 5
        self.motionProxy.angleInterpolation(rNames, rValues, rTimes, True)

        # Close hand
        self.motionProxy.setAngles(arm_side + "Hand", 0.1, 0.1)
        time.sleep(0.3)

        self.motionProxy.setStiffnesses(arm_side + "Arm", 0.0)


    def onTouched(self, strVarName, value):
        global memory
        logger.debug("Touched")
        memory.unsubscribeToEvent("TouchChanged", "NaoControl")
        for p in value:
            logger.debug(p)
            if p[1]:
                if p[0] == "RArm":
                    self.beg_for_token_finish("R")
                if p[0] == "LArm":
                    self.beg_for_token_finish("L")

    def beg_for_token_start(self, arm_side):
        self.logger.debug("Begging start. {}Arm".format(arm_side))
        if arm_side == "L":
            # left arm
            self.state.begging_left_arm = True
            self.state.begging_right_arm = False
            self.motionProxy.setStiffnesses("LArm", 1.0)
            self.motionProxy.setStiffnesses("RArm", 0.0)
            rNames = ["LShoulderPitch", "LShoulderRoll", "LElbowYaw", "LElbowRoll", "LWristYaw", "LHand"]
            rValues = [rad(-14.1),      rad(24.0),       rad(-77.9),  rad(-21.1),   rad(-104.5), 0.53]
        else:
            # right arm
            self.state.begging_right_arm = True
            self.state.begging_left_arm = False
            self.motionProxy.setStiffnesses("RArm", 1.0)
            self.motionProxy.setStiffnesses("LArm", 0.0)
            rNames = ["RShoulderPitch", "RShoulderRoll", "RElbowYaw", "RElbowRoll", "RWristYaw", "RHand"]
            rValues = [rad(-14.1),      rad(-24.0),      rad(77.9),   rad(21.1),    rad(104.5),  0.53]

        rTimes = [2.0] * 6
        self.motionProxy.angleInterpolation(rNames, rValues, rTimes, True)
        global memory
        memory.subscribeToEvent("TouchChanged", "NaoControl", "onTouched")


    def beg_for_token_finish(self, arm_side):
        self.logger.debug("Begging finish. {}Arm".format(arm_side))
        if (arm_side == "L" and self.state.begging_left_arm == True) or (arm_side == "R" and self.state.begging_right_arm == True):
            self.state.begging_left_arm = False
            self.state.begging_left_arm = False
            self.tts_say(["Fine", "Thanks", "OK. I got it.", "Let me play"])
            self.prepare_for_placement(self.state.next_placement)

    def prepare_for_placement(self, placement):
        field_id = placement[0]*3 + placement[1]
        self.logger.debug("Placing to {}".format(placement))
        if placement != -1:
            fields = [
                [16.5,  2.5, 15.0,-43.7,  0.7],  [16.5, 17.5,-22.0, 28.8, 11.9],  [25.4, -8.8,  3.0, 51.0,-15.9],

                [16.5, 16.0, 15.2,-78.5,  7.4],  [ 3.6,  8.9,-33.0, 68.8,  9.0],  [ 2.5,-10.0,-36.9, 80.2, -3.3],

                [-17.7,-7.6, 56.3,-88.5,-76.9],  [ 0.6, 13.0,-35.0, 87.5,  0.3],  [-13.6,-2.2,-51.7, 88.0, 73.4]
            ]

            #prepare to move to placement position
            effector_side = self.arm_responsible(placement)
            effector   = effector_side + "Arm"
            self.motionProxy.setStiffnesses(effector, 1.0)
            rNames = [effector_side + "ShoulderPitch", effector_side + "ShoulderRoll", effector_side + "ElbowYaw", effector_side + "ElbowRoll", effector_side + "WristYaw"]
            rValues = rad_array(fields[field_id])
            rTimes = [2.0] * len(rValues)
            self.motionProxy.angleInterpolation(rNames, rValues, rTimes, True)

            # Open hand
            self.motionProxy.setStiffnesses(effector, 1.0)
            self.motionProxy.setAngles(effector_side + "Hand", 0.80, 0.1)
            time.sleep(1.0)

            # Relax and close hand        
            self.relax_arm(effector_side)
        self.state.my_turn = False


    def configure_camera(self):
        '''
        configure_camera method is used to setup the camera proxy, subscribe to camera stream and establish the camera matrix.
        '''
        
        # Setup camera proxy to be used for image retrievals for later processing
        self.cameraProxy.setActiveCamera(xo_config_camera_id)
        self.video_client = self.cameraProxy.subscribeCamera("python_client", xo_config_camera_id, 2, 11, 5)

        self.logger.debug("Connection with camera established + video_client subscription configured.")
        
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
        '''
        take_a_look is used to take a snapshot from the camera view and format for later processing.
        '''
        nao_image = self.cameraProxy.getImageRemote(self.video_client)
        
        frame = np.asarray(bytearray(nao_image[6]), dtype=np.uint8)
        frame = frame.reshape((nao_image[1],nao_image[0],3))
        frame = frame[...,::-1]

        self.logger.debug("A camera snapshot was taken.")
        return frame


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
        
    def tts_say(self, texts):
        return self.tts.say(texts[random.randrange(len(texts))])
    
def rad(val):
    return val * almath.TO_RAD

def rad_array(arr):
    return [i * almath.TO_RAD for i in arr]


