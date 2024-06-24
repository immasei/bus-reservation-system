import json
import os
from pymongo import InsertOne
# https://www.mongodb.com/resources/languages/json-to-mongodb
def json_to_collection(filepath):
    collection = []
    with open(filepath, 'r') as f:
        data = json.load(f)
        key = list(data.keys())[0]
        for obj in data[key]:
            collection.append(InsertOne(obj))

    return collection

def load_data(conn):
    dirname = 'json_demo_data'
    for filename in os.listdir(dirname):
        filepath = f'{dirname}/{filename}'
        jsondata = json_to_collection(filepath)
        # set collection name = filename w/o ext
        basename = os.path.splitext(filename)[0]
        conn[basename].bulk_write(jsondata)