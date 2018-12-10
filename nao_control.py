from naoqi import ALProxy
from game_logging import GameLogger

class NaoControl:    

    def __init__(self, ip_address, port):        
        self.ip = ip_address
        self.port = port

        self.logger = GameLogger()

        # StandInit, SitRelax, StandZero, LyingBelly, Stand, Crouch, Sit
        self.base_position = "Crouch"
        self.logger.message("r", "Robot control initialized, default position set to " + self.base_position + " for efficient stability")
        

    def assume_initial_position(self):
        postureProxy = ALProxy("ALRobotPosture", self.ip, self.port)
        if postureProxy.getPosture() != self.base_position:
            id = postureProxy.goToPosture(self.base_position, 1.0)
            postureProxy.wait(id, 0)
        self.logger.message("r", "Initial position assumed")


    def find_target_position(self, section_id):
        print("Calculate target position")


    def select_hand(self, target_position):
        print("Choose active hand based on the target position")


    def forward_kinematics(self, active_hand):
        print("Calculate joint position - Forward Kinematics")


    def inverse_kinematics(self, target_position):
        print("Calculate kinematic chain of target position - Inverse Kinematics")


    def make_move(self, section_id):
        target_position = self.find_target_position(section_id)
        active_hand = self.select_hand(target_position)
        print("Request token / pick up the token")
        joint_position = self.forward_kinematics(active_hand)
        joint_target = self.inverse_kinematics(target_position)
        print("Execute the move")
        