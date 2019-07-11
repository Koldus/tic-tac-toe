'''
Definitions for the main program
Date: June 18, 2019

@author: mkoldus
'''

xo_config_robot_name = "Marvin"

# Initial Position 
xo_config_base_position = "Crouch"

# Camera Configurations
xo_config_camera_id = 1
"""
camera_matrix = [fx, fy, cx, cy, s] with:
    fx = focal lenght in x axis
    fy = focal length in y axis
    cx = image center in x axis
    cy = image center in y axis
    s  = skew factor (usually s=0)
Run the following command to retrieve the intrinsic parameters. Use 8x8 chess board or update the config file
> python camera_calibration.py
"""
xo_config_intrinsic_parameters = [888.52, 859.38, 666.72, 652.96, 0]

