import calendar
import datetime
import hashlib
import logging
import os
import subprocess

import rmc.shared.constants as c
import rmc.models as m

def _get_latest_user_schedule_item(user):
    return (m.UserScheduleItem
                .objects(user_id=user.id)
                .order_by("-$natural")
                .first())

def _get_screenshot_path(user, latest_user_schedule_item):
    if latest_user_schedule_item is None:
        return None

    stable_id = hashlib.md5(
                str(latest_user_schedule_item.id) +
                user.get_secret_id()
            ).hexdigest()
    return "static/schedules/%s.png" % stable_id

def _get_screenshot_filepath(user, latest_user_schedule_item):
    # TODO(jlfwong): This unfortunately leaves older screenshots lying around.
    # Perhaps it would be better to stick them under a folder per user and
    # delete all the unused schedules or store more information on the user.
    return os.path.join(c.RMC_ROOT, "server",
            _get_screenshot_path(user, latest_user_schedule_item))

def _get_term_start_month(dt):
    """Return a datetime for the start of the first month of the term of dt."""
    if dt.month <= 4:
        return datetime.datetime(dt.year, 1, 1)  # January

    if dt.month <= 8:
        return datetime.datetime(dt.year, 5, 1)  # May

    return datetime.datetime(dt.year, 9, 1)  # September

def _get_start_of_week(dt):
    """Return the datetime of the start of the week (Monday) of dt."""
    return dt - datetime.timedelta(days=dt.weekday())


def _get_best_screenshot_week(user, latest_user_schedule_item):
    """Return a datetime for the the best week to render for a given user."""
    term_start_dt = _get_term_start_month(latest_user_schedule_item.start_date)
    term_start_mon = _get_start_of_week(term_start_dt)

    best_week_date = None
    best_count_for_week = 0

    for weeknum in range(4):
        start_of_week = term_start_mon + datetime.timedelta(days=7 * weeknum)
        end_of_week = start_of_week + datetime.timedelta(days=7)
        q = m.UserScheduleItem.objects(user_id=user.id,
                                        start_date__gte=start_of_week,
                                        end_date__lte=end_of_week)

        count_for_week = q.count()

        if count_for_week > best_count_for_week:
            best_count_for_week = count_for_week
            # We use the date of the first item in the range instead of the
            # first date of the week to skirt around timezone issues.
            best_week_date = q.first().start_date

    assert best_week_date is not None
    return best_week_date

def update_screenshot_async(user):
    """Asynchronously take a screenshot of the schedule of the given user.

    If the user has no schedule or the screenshot is up to date, do nothing.
    """
    latest_usi = _get_latest_user_schedule_item(user)

    if latest_usi is None:
        return

    screenshot_filepath = _get_screenshot_filepath(user, latest_usi)

    if screenshot_filepath is None:
        return

    if os.path.exists(screenshot_filepath):
       return

    best_screenshot_week = _get_best_screenshot_week(user, latest_usi)

    start_date_timestamp = calendar.timegm(best_screenshot_week.timetuple())
    # JS timestamps are in milliseconds, not seconds
    start_date_timestamp_js = 1000 * start_date_timestamp
    url_to_render = ("%s/schedule/%s?start_date=%d" % (
                        c.RMC_HOST,
                        user.get_secret_id(),
                        start_date_timestamp_js))

    with open(os.devnull, 'w') as devnull:
        subprocess.Popen(
            [
                "phantomjs",
                "--disk-cache=true",
                os.path.join(os.path.dirname(__file__),
                        "phantom-schedule-screenshot.js"),
                url_to_render,
                screenshot_filepath
            ],
            stderr=devnull,
            stdout=devnull
        )


def get_screenshot_url(user, latest_user_schedule_item=None):
    """Return a full url, including protocol and domain, to schedule screenshot

    Return None if the screenshot isn't ready yet or the user has no schedule.
    """
    if latest_user_schedule_item is None:
        latest_user_schedule_item = _get_latest_user_schedule_item(user)

    screenshot_filepath = _get_screenshot_filepath(user,
        latest_user_schedule_item)

    # User has no schedule
    if screenshot_filepath is None:
        return None

    # Screenshot isn't rendered yet
    if not os.path.exists(screenshot_filepath):
        return None

    return c.RMC_HOST + "/" + _get_screenshot_path(user,
        latest_user_schedule_item)
