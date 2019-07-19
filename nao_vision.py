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
        return frame[y0:y1, x0:x1]

    
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


    def color_quantization(self, image_segment, K):
        Z = image_segment.reshape((-1,3))

        # convert to np.float32
        Z = np.float32(Z)

        # define criteria, number of clusters(K) and apply kmeans()
        criteria = (cv.TERM_CRITERIA_EPS + cv.TERM_CRITERIA_MAX_ITER, 10, 1.0)
        ret,label,center = cv.kmeans(Z,K,None,criteria,10,cv.KMEANS_RANDOM_CENTERS)

        # Now convert back into uint8, and make original image
        center = np.uint8(center)
        res = center[label.flatten()]
        return res.reshape((image_segment.shape))


    def calculate_color_ratio(self, masked_image):
        blue_count = np.count_nonzero(masked_image)
        total_count = masked_image.size
        return 100 * blue_count / total_count


    def analyze_color(self, image_segment):
        
        # Reduce the number of colors
        image_segment = self.color_quantization(image_segment, 8)
        
        # Convert the image to HSV
        hsv = cv.cvtColor(image_segment, cv.COLOR_BGR2HSV)

        # Threshold the HSV image to get only blue colors
        lower_blue = np.array([110,50,50])
        upper_blue = np.array([130,255,255])
        blue = cv.inRange(hsv, lower_blue, upper_blue)
        blue_pt = self.calculate_color_ratio(blue)

        # Declare the blue state if number of pixel is higher than 50%        
        if blue_pt > 30:
            return "blue"
        
        # Threshold the HSV image to get only blue colors
        lower_red = np.array([-20, 100, 100])
        upper_red = np.array([13, 255, 255])
        red = cv.inRange(hsv, lower_red, upper_red)
        red_pt = self.calculate_color_ratio(red)

        if red_pt > 30:
            return "red"

        return False


    def get_current_state(self, img):
        
        # Setup empty arrays for the current state
        current_state = [[0,0,0],[0,0,0],[0,0,0]]
        frames = [[None, None, None],[None, None, None],[None, None, None]]

        # Cut the board and store in a temp variable
        frames[0][0] = self.cut_image(img, 245, 50, 455, 230)
        frames[0][1] = self.cut_image(img, 490, 40, 730, 225)
        frames[0][2] = self.cut_image(img, 765, 40, 987, 220)
        frames[1][0] = self.cut_image(img, 200, 255, 435, 490)
        frames[1][1] = self.cut_image(img, 480, 255, 745, 485)
        frames[1][2] = self.cut_image(img, 780, 250, 1035, 480)
        frames[2][0] = self.cut_image(img, 140, 515, 400, 815)
        frames[2][1] = self.cut_image(img, 455, 510, 760, 820)
        frames[2][2] = self.cut_image(img, 810, 510, 1085, 820)
        
        # Stretch the image to a perfect square
        self.logger.debug("Image frame cutting completed")
        
        r = 0
        for row in frames:
            c = 0
            for cell in row:
                color = self.analyze_color(cell)

                if color == 'red':
                    current_state[r][c] = +1
                elif color == 'blue':
                    current_state[r][c] = -1

                c = c + 1
            
            r = r + 1
        
        # Stretch the image to a perfect square
        self.logger.debug("Current camera state: " + str(current_state))
        
        # Return the current state
        return current_state