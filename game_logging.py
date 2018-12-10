import json
import datetime

class GameLogger:

    def __init__(self):
        self.clean_logger()
        self.message("i", "Logging process initialized")


    def clean_logger(self):
        data = {
            "status" : "in_progress",
            "data" : []   
        }
        self.save_logger(data)


    def message(self, message_type, message_text):
        data = self.load_stored_data()
        now = datetime.datetime.now()
        new_log = { "id" : len(data['data']) + 1, "type" : message_type, "text" : message_text, "logged" : now.strftime("%H:%M:%S") }
        data['data'].append(new_log)
        self.save_logger(data)
    

    def save_logger(self, data):
        with open("html/data/logs.json", "w") as write_file:
            json.dump(data, write_file)
    

    def load_stored_data(self):
        data = None
        with open("html/data/logs.json", "r") as read_file:
            data = json.load(read_file)
        return data