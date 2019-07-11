import numpy as np
from naoqi import ALProxy
import almath
import cv2

from config import *
from nao_vision import NaoVision

class NaoControl:    
    '''
    Main class that controls the game and all interaction with the Nao robot.
    '''
    
    ## -------------------------------------------------------------
    #    MAIN FUNCTIONS
    ## -------------------------------------------------------------
    def __init__(self, ip_address, port, logging):        
        '''
        Constructor for NaoControl class, takes ip_address, port and name for comms with the Nao robot and a logger object.
        '''
        self.logger = logging

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

        self.logger.debug("Proxies with %s established", str(xo_config_robot_name))

        # Configure camera
        self.configure_camera()
        im = self.take_a_look()
        
        # Initiate the CV module 
        self.vision = NaoVision((im[0], im[1]), logging)

        # Assume the initial position and wait for the vision to be enabled
        self.assume_initial_position()

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
        rNames = ["RShoulderPitch", "RShoulderRoll", "RElbowYaw", "RElbowRoll"]
        rValues = [(10.3 * almath.TO_RAD), (-0.3 * almath.TO_RAD), (9.5 * almath.TO_RAD), (2.5 * almath.TO_RAD)]
        rTimes = [0.1, 0.1, 0.1, 0.1]
        # self.motionProxy.setAngles("RShoulderPitch", (10.3 * almath.TO_RAD), 0.1)
        # self.motionProxy.setAngles("RShoulderRoll", (-0.3 * almath.TO_RAD), 0.1)
        # self.motionProxy.setAngles("RElbowYaw", (9.5 * almath.TO_RAD), 0.1)
        # self.motionProxy.setAngles("RElbowRoll", (2.5 * almath.TO_RAD), 0.1)
        self.motionProxy.angleInterpolation(rNames, rValues, rTimes, True)

        # Wait until a board has been identified and complete the relaxed position


        # Close the initialization process
        self.logger.debug("Initial position assumed, default position set to " + xo_config_base_position + " for efficient stability")
        

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
        