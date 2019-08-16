from flask import Flask
import time

app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'Hello, World!'

@app.route('/long')
def get_long():
    time.sleep(10)
    return 'I slept well'