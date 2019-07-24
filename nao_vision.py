import cv2 as cv
import numpy as np
import time

'''
Open tasks:
- analyze the biggest blob

Embedded simplifications:
- image segments the analysis is performed on are hard-coded, it should be replaced with dymamic values returned from the board analysis
'''

class NaoVision:    

    def __init__(self, sizes, logging):
        self.camera_size = sizes
        self.board_visible = False

        self.logger = logging
        self.logger.debug("Computer vision initialized with the following camera size: %s",str(self.camera_size))



    def find_board(self, img):
        '''
        Function that analyzes camera input and searches for the board.
        returns ... True / False depending on the result
        '''
        
        # Pre-process the image for blob identification
        im_transformed = self.image_preprocessing(img)
        self.logger.debug("Image has been pre-processed for further analysis.")

        # Find the biggest blob
        biggest_blob, biggest_blob_size = self.find_biggest_blob(im_transformed)
        if( biggest_blob_size >= 650000 ):
            self.logger.debug("A sufficiently large blob has been identified. Image will now be cleaned.")

            # Remove anything outside the biggest blob
            im_cleaned = self.clean_image(im_transformed, biggest_blob)
            self.logger.debug("The image has been cleaned. Next line detection analysis will be performed.")

            # Determine if the biggest blob is indeed the 3x3 matrix we need
            lines, im_lines = self.find_lines(im_cleaned)
            
            # Check if the lines consitute a matrix
            if self.check_matrix(lines, im_lines):
                self.logger.info('Game board detected! Initiation sequence can now proceed further.')
                self.lines = lines
                return True, im_lines, biggest_blob_size
            
            return False, im_lines, biggest_blob_size

        self.logger.debug("No board identified. The biggest blog size found: %s",str(biggest_blob_size))
        return False, img, biggest_blob_size

        

    def get_current_state(self, img):
        '''
        Perform analysis of the requested image
        returns ... a current state of the board represented byt the standard array
                ... 0 represents and empy field
                ... +1 / -1 represents the two possible states
        '''
        
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
                color = self.analyze_color(cell, 20)

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


    
    ## -------------------------------------------------------------
    #    SUPPORTING FUNCTIONS
    ## -------------------------------------------------------------

    def split_lines(self, all_lines):
        '''
        Split the inserted lines into horizontal and vertical
        '''
        h_lines = []
        v_lines = []

        for line in all_lines:
            ln = line[0]
            theta = ln[1]
            b = np.sin(theta)

            if b >= 0.8:
                h_lines.append(line)
            else:
                v_lines.append(line)

        return h_lines, v_lines


    def get_line_intersect(self, line1, line2):
        '''
        Finds the intersection of two lines given in Hesse normal form.
        Returns closest integer pixel locations.
        '''
        rho1, theta1 = line1[0]
        rho2, theta2 = line2[0]
        A = np.array([
            [np.cos(theta1), np.sin(theta1)],
            [np.cos(theta2), np.sin(theta2)]
        ])
        b = np.array([[rho1], [rho2]])
        x0, y0 = np.linalg.solve(A, b)
        x0, y0 = int(np.round(x0)), int(np.round(y0))
        return [x0, y0]



    def check_matrix(self, lines, img):
        '''
        Check if hugh lines interesect into a 3x3 matrix
        Valid matrix consists of 8 lines (4 vertical and 4 horizontal) and each horizontal line crosses exactly four vertical lines.
        '''
        valid_matrix = True

        # Make sure there is exactly eight significant lines in the picture
        if( lines.shape[0] == 8 ):
            
            # Split horizontal and vertical lines
            h_lines, v_lines = self.split_lines(lines)
            
            # Make sure there is four of each
            if len(h_lines) == 4 and len(v_lines) == 4:

                # Make sure each horizontal line intersects precisely 4 vertical lines
                for h_line in h_lines:
                    intersect_num = 0
                    
                    for v_line in v_lines:
                        intersect = self.get_line_intersect(h_line, v_line)
                        
                        # Intersect is only valid, if the intersection falls within the image dimensions
                        if img.shape[1] >= intersect[0] >= 0 and img.shape[0] >= intersect[1] >= 0:
                            intersect_num = intersect_num + 1

                    if intersect_num != 4:
                        self.logger.debug('Matrix detection failed. One of the horizontal lines has failed to identify four intersects')
                        valid_matrix = False
            
            else:
                self.logger.debug('Matrix detection failed. Detected ' + str(len(h_lines)) + ' horizontal and ' + str(len(v_lines)) + ' vertical lines')
                valid_matrix = False
        
        else:
            self.logger.debug('Matrix detection failed. Number of lines detected is: ' + lines.shape[0] )
            valid_matrix = False

        return valid_matrix


    
    def draw_lines(self, line, img):
        '''
        Helper function to visualize the board lines
        '''
        rho = line[0]
        theta = line[1]
        
        a = np.cos(theta)
        b = np.sin(theta)

        x0 = a*rho
        y0 = b*rho

        x1 = int(x0 + 2000*(-b))
        y1 = int(y0 + 2000*(a))
        x2 = int(x0 - 2000*(-b))
        y2 = int(y0 - 2000*(a))
        
        img = cv.line(img, (x1, y1), (x2, y2), (255,0,255), 2)
        return img



    def get_points_on_line(self, line, img):
        rho = line[0]
        theta = line[1]

        point1 = [0,0]
        point2 = [0,0]

        if( theta > np.pi*45/180 and theta < np.pi*135/180):
            # Horizontal lines
            point1[0] = 0
            point1[1] = rho / np.sin(theta)
            point2[0] = img.shape[1]
            point2[1] = -img.shape[1]/np.tan(theta) + rho/np.sin(theta)
        else:
            # Vertical lines
            point1[0] = rho / np.cos(theta)
            point1[1] = 0
            point2[0] = -img.shape[0]/np.tan(theta) + rho/np.cos(theta)
            point2[1] = img.shape[0]

        return point1, point2



    def merge_lines(self, lines, img):
        '''
        Perform k-means to group similar lines
        ''' 

        sd = np.std(lines, axis = 0)
        lines = lines / sd

        criteria = (cv.TERM_CRITERIA_EPS, 10, 1.0)
        ret,label,center = cv.kmeans(lines,8,None,criteria,10,cv.KMEANS_PP_CENTERS)

        # Reformat the output from k-means
        merged_lines = []
        for line in center:
            merged_lines.append([line])

        return merged_lines * sd



    def find_lines(self, im_cleaned):
        '''
        Perform Hugh Linear Transformation to detect if there are lines in the identified blob
        '''
        # Perform hough transformation, optimize threshold to only consider lines that are significant
        threshold = 500
        lines = cv.HoughLines(im_cleaned, 1, np.pi/180, threshold)
        
        # Merge neigboring lines together
        merged_lines = self.merge_lines(lines, im_cleaned)

        # Display merged lines
        ret = cv.cvtColor(im_cleaned, cv.COLOR_GRAY2RGB)
        for line in merged_lines:
            ret = self.draw_lines(line[0], ret)

        return merged_lines, ret



    def find_biggest_blob(self, im_transformed):
        '''
        Function to identify the biggest blob an its size
        '''

        # Find image contours
        ret,thresh = cv.threshold(im_transformed,127,255,0)
        im_cont, contours, hierarchy = cv.findContours(thresh,cv.RETR_TREE,cv.CHAIN_APPROX_SIMPLE)
        
        # Loop over contours to find the biggest area
        c = 0
        largest_area = 0
        largest_contour = 0
        for contour in contours:
            area = cv.contourArea(contour)
            if( area > largest_area ):
                largest_area = area
                largest_contour = c
            c = c + 1
        
        # # Render the contours
        # ret = cv.cvtColor(im_cont, cv.COLOR_GRAY2RGB)
        # cv.drawContours(ret,contours,largest_contour,(255,0,255), 3)
        
        return [contours[largest_contour]], largest_area



    def clean_image(self, im_transformed, biggest_blob):
        '''
        Remove clutter outside the biggest blob
        '''

        # Copy the thresholded image.
        stencil = np.zeros(im_transformed.shape).astype(im_transformed.dtype)

        # Create image mask based on the contour of the biggest blob
        cv.fillPoly(stencil, biggest_blob, [255, 255, 255])
        
        # Apply mask on the original image
        result = cv.bitwise_and(im_transformed, stencil)

        # Erode the image back to balance the original dilation
        result = cv.erode(result, np.ones((5,5), np.uint8))

        return result
        
    
    
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
        im_transformed = cv.dilate(im_temp, np.ones((5,5), np.uint8), iterations = 1)

        return im_transformed



    def cut_image(self, frame, x0, y0, x1, y1):
        '''
        Function that returns an image segment.
        '''
        return frame[y0:y1, x0:x1]



    def color_quantization(self, image_segment, K):
        '''
        Perform k-means clustering to limit the number of colors
        '''
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
        '''
        Calculate the ratio of masked color as a percentage from all pixels.
        '''
        color_count = np.count_nonzero(masked_image)
        total_count = masked_image.size
        return 100 * color_count / total_count



    def analyze_color(self, image_segment, threshold):
        '''
        Perform color analysis on an image segment in the quantity surprasing the requested threshold.
        - image_segment ... picture segment to be analyzed
        - threshold ... numeric value, in percentages required for significant color
        returns ... False if required colors are not present
                ... 'blue' / 'red' if color is identified 
        '''

        # Reduce the number of colors
        image_segment = self.color_quantization(image_segment, 8)
        
        # Convert the image to HSV
        hsv = cv.cvtColor(image_segment, cv.COLOR_BGR2HSV)

        # Threshold the HSV image to get only blue colors
        lower_blue = np.array([100,100,50])
        upper_blue = np.array([135,255,255])
        blue = cv.inRange(hsv, lower_blue, upper_blue)
        blue_pt = self.calculate_color_ratio(blue)

        # Declare the blue state if number of pixel is higher than 50%        
        if blue_pt > threshold:
            return "blue"
        
        # Threshold the HSV image to get only blue colors
        lower_red1 = np.array([-20, 100, 100])
        upper_red1 = np.array([20, 255, 255])
        red1 = cv.inRange(hsv, lower_red1, upper_red1)
        lower_red2 = np.array([155, 100, 100])
        upper_red2 = np.array([180, 255, 255])
        red2 = cv.inRange(hsv, lower_red2, upper_red2)
        red_combined = red1 + red2
        red_pt = self.calculate_color_ratio(red_combined)

        if red_pt > threshold:
            return "red"

        return False