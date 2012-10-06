from datetime import datetime
import logging
import time

LOG_CATEGORY_TRANSCRIPT = 'TRANSCRIPT'
LOG_EVENT_UPLOAD = 'UPLOAD'
LOG_EVENT_REMOVE = 'REMOVE'

LOG_CATEGORY_DATA_MODEL = 'DATA_MODEL'
LOG_EVENT_UNKNOWN_COURSE_ID = 'UNKNOWN_COURSE_ID'

# TODO(Sandy): Do better logging
# E.g. log_event('TRANSCRIPT', 'REMOVE', { 'user_id': ID_HERE })
def log_event(category, event_name, data=None):
    now = time.time()
    human_time = datetime.fromtimestamp(now)

    log_msg = "Event Logged at %s[%s]: %s %s" % (human_time, now, category,
        event_name)

    if data:
        log_msg += " %s" % data

    logging.info(log_msg)
