import numpy as np
from naoqi import ALProxy
import almath
import cv2
import random
import functools

from config import *
from nao_vision import NaoVision

class State:
    def __init__(self):
        begging_left_arm = False
        begging_right_arm = False

class NaoControl:    
    '''
    Main class that controls the game and all interaction with the Nao robot.
    '''
    
    SAY_TOKEN_GIVEN = ["Fine", "Thanks", "OK. I got it.", "Let me play"]


    ## -------------------------------------------------------------
    #    MAIN FUNCTIONS
    ## -------------------------------------------------------------
    def __init__(self, ip_address, port, logging):        
        '''
        Constructor for NaoControl class, takes ip_address, port and name for comms with the Nao robot and a logger object.
        '''
        self.logger = logging
        self.state = State()

        # Setup variables for managing the game flow
        self.init_completed = False
        self.game_ready = False
        self.result = -1
        
        # Setup proxies to enable message exchange with the robot
        self.autoProxy = ALProxy("ALAutonomousLife", ip_address, port)
        self.awarenessProxy = ALProxy("ALBasicAwareness", ip_address, port)
        self.postureProxy = ALProxy("ALRobotPosture", ip_address, port)
        self.motionProxy = ALProxy("ALMotion", ip_address, port)
        self.cameraProxy = ALProxy("ALVideoDevice", ip_address, port)
        self.tts = ALProxy("ALTextToSpeech")
        self.memory_service = ALProxy("ALMemory")
        self.touch = self.memory_service.subscriber("TouchChanged")
        self.id = self.touch.signal.connect(functools.partial(self.onTouched, "TouchChanged"))

        self.logger.debug("Proxies with %s established", str(xo_config_robot_name))

        # Configure camera
        self.configure_camera()
        im = self.take_a_look()
        
        # Initiate the CV module 
        self.vision = NaoVision((im[0], im[1]), logging)

        # Assume the initial position and wait for the vision to be enabled
        self.assume_initial_position()

        # Listen for touch
        
        # Confirm the initialization process has been concluded 
        self.init_completed = True



    def begin_game(self):
        self.game_ready = True

    
    ## -------------------------------------------------------------
    #    SUPPORTING FUNCTIONS
    ## -------------------------------------------------------------

    def assume_initial_position(self):
        '''
        Constructor for NaoControl class, takes ip_address and port for comms with the Nao robot and a logger object.
        '''
        board_visible = False
        
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
        self.motionProxy.setStiffnesses("Head", 0.0)
        self.motionProxy.setAngles("HeadPitch", (29 * almath.TO_RAD), 0.1)
        self.motionProxy.setStiffnesses("Head", 1.0)

        # Configure arms to the right position
        self.motionProxy.setStiffnesses("RArm", 0.0)
        self.motionProxy.setStiffnesses("LArm", 0.0)


        rNames = ["RShoulderPitch", "RShoulderRoll", "RElbowYaw", "RElbowRoll", "RWristYaw", "LShoulderPitch", "LShoulderRoll", "LElbowYaw", "LElbowRoll", "LWristYaw"]

        rValues = [(48.0 * almath.TO_RAD), (1.0 * almath.TO_RAD), (85.0 * almath.TO_RAD), (-48.0 * almath.TO_RAD), (5.0 * almath.TO_RAD),
                   (48.0 * almath.TO_RAD), (1.0 * almath.TO_RAD), (85.0 * almath.TO_RAD), ( 48.0 * almath.TO_RAD), (5.0 * almath.TO_RAD)]
        rTimes = [2.0] * 8
        self.motionProxy.angleInterpolation(rNames, rValues, rTimes, True)
        self.motionProxy.setStiffnesses("RArm", 0.0)
        self.motionProxy.setStiffnesses("LArm", 0.0)

        # Wait until a board has been identified and complete the relaxed position


        # Close the initialization process
        self.logger.debug("Initial position assumed, default position set to " + xo_config_base_position + " for efficient stability")
        

    def onTouched(self, strVarName, value):
        for p in value:
            if p[1] and p[0] in ["LArm", "RArm"]:
                self.beg_for_token_finish()

    def beg_for_token_start(self, isLeftArm):
        self.motionProxy.setStiffnesses("RArm", 1.0)
        self.motionProxy.setStiffnesses("LArm", 1.0)
        if isLeftArm:
            # left arm
            state.begging_left_arm = True
            state.begging_right_arm = False
            rNames = ["LShoulderPitch", "LShoulderRoll", "LElbowYaw", "LElbowRoll", "LWristYaw", "LHand"]
            rValues = [rad(-14.1),      rad(24.0),       rad(-77.9),  rad(-21.1),   rad(-104.5), rad(0.53)]
        else:
            # right arm
            state.begging_right_arm = True
            state.begging_left_arm = False
            rNames = ["RShoulderPitch", "RShoulderRoll", "RElbowYaw", "RElbowRoll", "RWristYaw", "RHand"]
            rValues = [rad(-14.1),      rad(-24.0),      rad(77.9),   rad(21.1),    rad(104.5),  rad(0.53)]

        rTimes = [2.0] * 12
        self.motionProxy.angleInterpolation(rNames, rValues, rTimes, True)

    def beg_for_token_finish(self, isLeftArm):
        if (isLeftArm == True and state.begging_left_arm == True) or (isLeftArm == False and state.begging_right_arm == True):
            self.motionProxy.setStiffnesses("RArm", 0.0)
            self.motionProxy.setStiffnesses("LArm", 0.0)
            state.begging_left_arm = False
            state.begging_left_arm = False
            self.touch.signal.disconnect(self.id)
            self.tts.say(self.SAY_TOKEN_GIVEN[random.randrange(len(self.SAY_TOKEN_GIVEN))])
            self.id = self.touch.signal.connect(functools.partial(self.onTouched, "TouchChanged"))


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