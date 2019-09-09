import cv2 as cv
import numpy as np
import time
import os

'''
Open tasks:
- analyze the biggest blob

Embedded simplifications:
- image segments the analysis is performed on are hard-coded, it should be replaced with dymamic values returned from the board analysis
'''

class NaoVision:

    img_camera = None
    img_lines = None
    img_rectified = None
    img_current_state = None

    def __init__(self, sizes, logging):
        self.logger = logging
        self.logger.debug("Computer vision initialized with the following camera size: %s",str(sizes))



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
        if( biggest_blob_size >= 140000 ):
            self.logger.debug("A sufficiently large blob has been identified. Image will now be cleaned.")

            # Remove anything outside the biggest blob
            im_cleaned = self.clean_image(im_transformed, biggest_blob)
            self.logger.debug("The image has been cleaned. Next line detection analysis will be performed.")

            # Determine if the biggest blob is indeed the 3x3 matrix we need
            lines, im_lines = self.find_lines(im_cleaned, 200)

            # Check if the lines consitute a matrix
            if self.check_matrix(lines, im_lines):
                self.logger.debug('Game board detected.')
                return True, im_cleaned, biggest_blob_size
            
            return False, im_lines, biggest_blob_size

        self.logger.debug("No board identified. The biggest blog size found: %s",str(biggest_blob_size))
        return False, img, biggest_blob_size

        

    def fix_board_position(self, img):
        '''
        Takes current board position and freezes it in memory.
        '''
        # Retrieve ordered horizontal and vertical lines
        lines, im_lines = self.find_lines(img, 200)
        h_lines, v_lines = self.split_lines(lines)

        # Order lines and pick to find the outer edges
        h_lines_ordered = self.order_lines(h_lines, True)
        v_lines_ordered = self.order_lines(v_lines, False)

        self.lines = [h_lines_ordered, v_lines_ordered]

        # Store image corners in memory
        tl, tr, bl, br = self.find_corners(h_lines_ordered, v_lines_ordered)
        self.corners = np.array([ tl, tr, br, bl ], dtype = "float32")
        
        # Store image segments dimensions in memory
        self.dimensions = self.find_all_segments(h_lines_ordered, v_lines_ordered)

        # Calculate the pixel dimensions of the identified board
        width_bottom = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
        width_up = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
        height_right = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
        height_left = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))

        # Take the maximum of the width and height values a the final dimensions
        self.matrix_dim = max(int(width_up), int(height_right), int(width_bottom), int(height_left)) - 1
        
        # Construct destination points for correct image
        self.matrix_destination = np.array([ [0, 0], [self.matrix_dim, 0], [self.matrix_dim, self.matrix_dim], [0, self.matrix_dim] ], dtype = "float32")

        self.logger.debug("The image coordinates have been fixed. Do not move the board from this point forward.")
        return(im_lines)


    def get_current_state(self, img):
        '''
        Perform analysis of the requested image
        returns ... a current state of the board represented byt the standard array
                ... 0 represents and empy field
                ... +1 / -1 represents the two possible states
        '''
        color_threshold = 20
        ignore_margin_pt = 10

        # Store image with lines and intersects
        im_lines = self.image_preprocessing(img)
        im_lines = cv.cvtColor(im_lines, cv.COLOR_GRAY2RGB)

        for line in self.lines[0] + self.lines[1]:
            im_lines = self.draw_lines(line[0], im_lines)
        
        cv.imwrite(os.path.join("static/data", "lines.jpg"), im_lines)
        self.img_lines = cv.imencode(".jpg", im_lines)

        
        # Store image for dashboard
        cv.imwrite(os.path.join("static/data", "raw_image.jpg"), img)

        # Re-shape the image to correct for the perspective
        M = cv.getPerspectiveTransform(self.corners, self.matrix_destination)
        warp = cv.warpPerspective(img, M, (self.matrix_dim, self.matrix_dim))
        
        # Store image for dashboard
        cv.imwrite(os.path.join("static/data", "current_state_raw.jpg"), warp)
        
        # Setup empty arrays for the current state
        current_state = [[0,0,0],[0,0,0],[0,0,0]]
        frames = [[None, None, None],[None, None, None],[None, None, None]]

        # Configure offsets for cutting the image
        field_size = int(self.matrix_dim / 3)
        ignore_margin_size = ignore_margin_pt * field_size / 100
        field_size_reduced = field_size - 2 * ignore_margin_size
        offset_1 = ignore_margin_size
        offset_2 = ignore_margin_size + field_size_reduced
        offset_3 = field_size + ignore_margin_size
        offset_4 = 2 * field_size - ignore_margin_size
        offset_5 = 2 * field_size + ignore_margin_size
        offset_6 = 3 * field_size - ignore_margin_size

        # Cut the board and store in a temp variable
        frames[0][0] = self.cut_image(warp, [offset_1, offset_1, offset_2, offset_2])
        frames[0][1] = self.cut_image(warp, [offset_3, offset_1, offset_4, offset_2])
        frames[0][2] = self.cut_image(warp, [offset_5, offset_1, offset_6, offset_2])
        frames[1][0] = self.cut_image(warp, [offset_1, offset_3, offset_2, offset_4])
        frames[1][1] = self.cut_image(warp, [offset_3, offset_3, offset_4, offset_4])
        frames[1][2] = self.cut_image(warp, [offset_5, offset_3, offset_6, offset_4])
        frames[2][0] = self.cut_image(warp, [offset_1, offset_5, offset_2, offset_6])
        frames[2][1] = self.cut_image(warp, [offset_3, offset_5, offset_4, offset_6])
        frames[2][2] = self.cut_image(warp, [offset_5, offset_5, offset_6, offset_6])

        # Stretch the image to a perfect square
        self.logger.debug("Image frame cutting completed")
        
        r = 0
        for row in frames:
            c = 0
            for cell in row:
                color = self.analyze_color(cell, color_threshold)

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

    def find_all_segments(self, h_lines, v_lines):
        c = 0
        segments = []
        while c < 3:
            
            column = []
            r = 0
            while r < 3:
                # Select only related lines
                h_lines_subset = [ h_lines[r], h_lines[r+1] ]
                v_lines_subset = [ v_lines[c], v_lines[c+1] ]
                tl, tr, bl, br = self.find_corners(h_lines_subset, v_lines_subset)

                column.append([tl, tr, bl, br])
                r = r + 1

            segments.append(column)
            c = c + 1
        
        return segments


    def find_corners(self, h_lines, v_lines):
        '''
        Convert outer edges to four corner points.
        '''
        tl = self.get_line_intersect( h_lines[0], v_lines[0] )
        tr = self.get_line_intersect( h_lines[0], v_lines[-1] )
        br = self.get_line_intersect( h_lines[-1], v_lines[-1] )
        bl = self.get_line_intersect( h_lines[-1], v_lines[0] )
        return tl, tr, bl, br


    
    def order_lines(self, lines, horizontal):
        '''
        Takes in lines and return them order from closest to the most distant from the origin. 
        '''
        simple_array = []
        for line in lines:
            rho, theta = line[0]

            # Calculate intersect with the respective axis
            if horizontal:
                intersect = rho * np.sin(theta)
            else:
                intersect = rho * np.cos(theta)
            
            # Added into the simple array for ordering
            simple_array.append((rho, theta, intersect))

        # Add labels and order lines
        structured_array = np.array(simple_array, dtype=[('rho', float), ('theta', float), ('intersect', float)])
        ordered_array = np.sort(structured_array, order='intersect')

        # Re-format the outcome into OpenCV line structure
        final_array = []
        for line in ordered_array:
            final_array.append([[line[0], line[1]]])

        return final_array


    
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
        return (x0, y0)



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



    def find_lines(self, im_cleaned, threshold):
        '''
        Perform Hugh Linear Transformation to detect if there are lines in the identified blob
        '''
        # Perform hough transformation, optimize threshold to only consider lines that are significant
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



    def cut_image(self, frame, segment_dim):
        '''
        Function that returns an image segment.
        '''
        x0, y0, x1, y1 = segment_dim
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



    def renderImage(self, state):
        field_size = 200
        image_size = 3 * field_size

        img = np.zeros((image_size,image_size,3),np.uint8)
        
        r = 0
        for row in state:
            offset_y = field_size * r
            c = 0
            for cell in row:
                offset_x = field_size * c
                
                x0 = offset_x
                y0 = offset_y
                x1 = offset_x + field_size
                y1 = offset_y + field_size

                # Fill the frame based on the value
                if cell == 1:
                    cv.rectangle(img, (x0, y0), (x1, y1), (0, 0, 255), -1)
                elif cell == -1:
                    cv.rectangle(img, (x0, y0), (x1, y1), (255, 0, 0), -1)
                else:
                    cv.rectangle(img, (x0, y0), (x1, y1), (255, 255, 255), -1)
                
                # Draw a frame
                cv.rectangle(img, (x0, y0), (x1, y1), (0, 0, 0), 10)
                c = c + 1
            
            r = r + 1

        cv.imwrite(os.path.join("static/data", "game_state.jpg"), img)



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