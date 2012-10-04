from bson import json_util

def json_loads(json_str):
    return json_util.loads(json_str)

def json_dumps(obj):
    return json_util.dumps(obj).replace('</', '<\\/')

def dict_to_list(dikt):
    update_with_name = lambda key, val: dict(val, **{ 'name': key })
    return [update_with_name(k, v) for k, v in dikt.iteritems()]
