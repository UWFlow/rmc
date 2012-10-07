import logging

LOG_CATEGORY_TRANSCRIPT = 'TRANSCRIPT'
LOG_EVENT_UPLOAD = 'UPLOAD'
LOG_EVENT_REMOVE = 'REMOVE'

LOG_CATEGORY_DATA_MODEL = 'DATA_MODEL'
LOG_EVENT_UNKNOWN_COURSE_ID = 'UNKNOWN_COURSE_ID'

LOG_CATEGORY_COURSE_SEARCH = 'COURSE_SEARCH'
LOG_EVENT_SEARCH_PARAMS = 'SEARCH_PARAMS'

# TODO(Sandy): Do better logging
# E.g. log_event('TRANSCRIPT', 'REMOVE', { 'user_id': ID_HERE })
def log_event(category, event_name, data=None):
    log_msg = "Event Logged: %s %s" % (category, event_name)

    if data:
        log_msg += " %s" % data

    logging.info(log_msg)
