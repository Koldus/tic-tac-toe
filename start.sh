#!/bin/sh

echo "* ----------------------------------------------- *"
echo "*                                                 *"
echo "*    Open dashboard at http://localhost:5000/     *"
echo "*                                                 *"
echo "* ----------------------------------------------- *"


export FLASK_APP=main.py
export FLASK_ENV=development
flask run
