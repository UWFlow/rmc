import hashlib
import os
import subprocess

import rmc.shared.constants as c
import rmc.models as m

class _NoSchedule(Exception):
    pass

def _get_screenshot_path(user):
    latest_user_schedule_item = m.UserScheduleItem.objects(
                user_id=user.id).order_by("-$natural").limit(1)

    if len(latest_user_schedule_item) == 0:
        raise _NoSchedule("User has no schedule")
    else:
        latest_user_schedule_item = latest_user_schedule_item[0]

    stableid = hashlib.md5(
                str(latest_user_schedule_item.id) +
                user.get_secret_id()
            ).hexdigest()
    return "static/schedules/%s.png" % stableid

def _get_screenshot_filepath(user):
    return os.path.join(c.RMC_ROOT, "server", _get_screenshot_path(user))

def update_screenshot_async(user):
    """Asynchronously take a screenshot of the schedule of the given user.

    If the user has no schedule or the screenshot is up to date, do nothing.
    """
    script_path = os.path.join(os.path.dirname(__file__),
            "phantom-schedule-screenshot.js")
    url_to_render = c.RMC_HOST + "/schedule/" + user.get_secret_id()

    try:
        screenshot_filepath = _get_screenshot_filepath(user)
    except _NoSchedule:
        return

    if os.path.exists(screenshot_filepath):
        return

    # TODO(jlfwong): This unfortunately leaves older screenshots lying around.
    # Perhaps it would be better to stick them under a folder per user and
    # delete all the unused schedules or store more information on the user.

    with open(os.devnull, 'w') as devnull:
        subprocess.Popen(
            [
                "phantomjs",
                "--disk-cache=true",
                script_path,
                url_to_render,
                screenshot_filepath
            ],
            stderr=devnull,
            stdout=devnull
        )

def get_screenshot_url(user):
    """Return a full url, including protocol and domain, to schedule screenshot

    Return None if the screenshot isn't ready yet or the user has no schedule.
    """
    try:
        if os.path.exists(_get_screenshot_filepath(user)):
            return c.RMC_HOST + "/" + _get_screenshot_path(user)
        else:
            return None
    except _NoSchedule:
        return None
