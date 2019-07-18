import cv2 as cv
import numpy as np
import time

class NaoVision:    

    def __init__(self, sizes, logging):
        self.camera_size = sizes
        self.board_visible = False

        self.logger = logging
        self.logger.debug("Computer vision initialized with the following camera size: %s",str(self.camera_size))


    def find_board(self, img):
        # time.sleep(1.0)
        
        # Pre-process the image for blob identification
        im_transformed = self.image_preprocessing(img)

        # Set up the detector with default parameters.
        params = cv.SimpleBlobDetector_Params()

        params.filterByColor = True
        params.blobColor = 255

        params.filterByArea = True
        params.minArea = 1000

        params.filterByCircularity = False
        params.minCircularity = 0.5

        params.filterByConvexity = False
        params.filterByInertia = False

        detector = cv.SimpleBlobDetector_create(params)

        # Detect blobs
        keypoints = detector.detect(im_transformed)
        
        # Draw detected blobs as red circles
        im_with_keypoints = cv.drawKeypoints(im_transformed, keypoints, np.array([]), (0,0,255), cv.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)
        
        cv.imshow("Keypoints", im_with_keypoints)
        cv.waitKey(0)
        
        return True


    
    ## -------------------------------------------------------------
    #    SUPPORTING FUNCTIONS
    ## -------------------------------------------------------------

    def image_preprocessing(self, im_orig):
        '''
        Apply several transformation to preprocess image for blob identification.
        The following filters are applied: convert to grayscale, gaussian blur, adaptive thresholding, bitwise invert and dilating
        '''

        # Convert to grayscale
        im_temp = cv.cvtColor(im_orig, cv.COLOR_BGR2GRAY)

        # Apply gaussian blur to smooth the lines by removing noise
        im_temp = cv.GaussianBlur(im_temp, (11,11), 0)

        # Apply adaptive image thresholding
        # ... it calculates a mean over a 5x5 window and subtracts 2 from the mean. This is the threshold level for every pixel.
        im_temp = cv.adaptiveThreshold(im_temp, 255, cv.ADAPTIVE_THRESH_MEAN_C, cv.THRESH_BINARY, 5, 2)

        # Invert the image
        im_temp = cv.bitwise_not(im_temp)

        # Dilate the image to complete small cracks
        im_transformed = cv.dilate(im_temp, np.ones((10,10), np.uint8), iterations = 1)

        return im_transformed



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