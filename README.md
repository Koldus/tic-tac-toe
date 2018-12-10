# Nao Playing Tic-Tac-Toe

## Setup the robot

1. Make sure your laptop and your robot are on the same network (internet connection is not required)
2. Choregraphe folder containing supporting behaviors must be installed prior running the skill
3. Parts folder containing blueprints for your 3D-printed game tokens (representing Xs and Os), plus a guide on how to create and setup the board so that the parts fit and the robot can reach all fields.
4. Clone the repository

```
git clone 
cd ./tic-tac-toe
```

Make sure you install and test all dependencies before running the game. Details are described below.

5. Setup the config file
6. Finally, run the game

```
python main.py
```

Optionally, review the Papers folder to study theory that we implemented in this study.

## Install Dependencies

- Python 2.7.* (erequired by the pynaoqi SDK), tested on version 2.7.15

```
conda create -n nao python=2.7
source activate nao
```

- Numpy, tested on version 1.15.0

```
pip install --upgrade pip
pip install numpy
```

- OpenCV, tested on version 3.4.2.17

```
pip install opencv-python
```

- pynaoqi

```

```

... and make sure everything works as it should be:

```
python
>>> import numpy
>>> import cv2
```

## References

A lot of inspiration has been derived from the following resources:

- []()