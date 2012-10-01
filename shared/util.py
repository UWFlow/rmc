from bson import json_util

def json_loads(json_str):
    return json_util.loads(json_str)

def json_dumps(obj):
    return json_util.dumps(obj).replace('</', '<\\/')
