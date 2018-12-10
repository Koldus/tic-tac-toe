from naoqi import ALProxy
from game_logging import GameLogger

class NaoVision:    

    def __init__(self, ip_address, port):        
        self.ip = ip_address
        self.port = port
        
        self.logger = GameLogger()
        self.logger.message("c", "Robot vision initialized")

    
    def create_proxy(self):
        self.cam = ALProxy("ALPhotoCapture", self.ip, self.port)
        self.cam.setCameraID(1)
        self.cam.setPictureFormat('jpg')
        self.cam.setResolution(2)
        self.logger.message("c", "Robot vision proxy created")


    def connect_dev_camera(self):
        self.logger.message("c", "Robot vision proxy created")
        

    def cut_image(self, frame, x0, y0, x1, y1):
        return frame[x0:y0, x1:y1]

    
    def initialize_board(self):
        print("Search for the board -> memorize the coordinates")
        print("Stretch the image to a perfect square")
        self.image_borders = {"x0": 0, "y0": 0, "x1": 0, "y1": 0}
        print("Identify 9 segments, one for each field of the board -> lock it down")
        self.image_segments = {
            "segment1": {"x0": 0, "y0": 0, "x1": 0, "y1": 0},
            "segment2": {"x0": 0, "y0": 0, "x1": 0, "y1": 0},
            "segment3": {"x0": 0, "y0": 0, "x1": 0, "y1": 0},
            "segment4": {"x0": 0, "y0": 0, "x1": 0, "y1": 0},
            "segment5": {"x0": 0, "y0": 0, "x1": 0, "y1": 0},
            "segment6": {"x0": 0, "y0": 0, "x1": 0, "y1": 0},
            "segment7": {"x0": 0, "y0": 0, "x1": 0, "y1": 0},
            "segment8": {"x0": 0, "y0": 0, "x1": 0, "y1": 0},
            "segment9": {"x0": 0, "y0": 0, "x1": 0, "y1": 0},
        }
        print("Trigger start of the game event")
    

    def analyze_color(self, image_segment):
        print("Perform color analysis to identify the dominant color")
        return "red"


    def get_current_state(self):
        
        # Setup an empty array for the current state
        current_state = [0,1,2,3,4,5,6,7,8]
        
        # Take the camera snapshots
        frame = self.cam.takePicture()

        # Cut the board out of the taken frame
        frame_cut = self.cut_image(frame, self.image_borders.x0, self.image_borders.y0, self.image_borders.x1, self.image_borders.y1)
        
        # Stretch the image to a perfect square
        print("Stretch the image to a perfect square")
        
        i=0
        for segment in self.image_segments:
            
            # Retrieve the segment dimensions
            segment = self.image_segments.get( "segment"+str(i) )
            
            # Cut image segment out of the frame cut
            image_segment = self.cut_image(frame_cut, segment.x0, segment.y0, segment.x1, segment.y1)
            
            # Identify color from the image segment
            identified_color = self.analyze_color(image_segment)

            # Update segment's state based on the results
            if identified_color == self.my_color:
                current_state[i] = "x"
            elif identified_color == self.oponent_color:
                current_state[i] = "o"
            
            i = i + 1
        
        # Return the current state
        print(current_state)
        return current_state