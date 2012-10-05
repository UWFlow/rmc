from bson import json_util
import rmc.shared.constants as c

def json_loads(json_str):
    return json_util.loads(json_str)

def json_dumps(obj):
    return json_util.dumps(obj).replace('</', '<\\/')

def dict_to_list(dikt):
    update_with_name = lambda key, val: dict(val, **{ 'name': key })
    return [update_with_name(k, v) for k, v in dikt.iteritems()]

def get_current_term_id():
    # FIXME[2013](Sandy): Don't hardcode this. Get the current term from the time
    # REMEMBER TO DO THIS BEFORE 2013_01
    return c.CURRENT_TERM_ID
