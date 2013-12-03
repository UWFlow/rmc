import calendar
import datetime
import functools
import hashlib
import logging
import multiprocessing
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
    urlpath = _get_screenshot_path(user, latest_user_schedule_item)

    if urlpath is None:
        return None

    filepath = os.path.abspath(os.path.join(c.RMC_ROOT, "server", urlpath))
    schedule_symlink_dir = os.path.dirname(filepath)
    schedule_storage_dir = os.path.join(c.SHARED_DATA_DIR, "schedules")

    if not os.path.exists(schedule_storage_dir):
        os.makedirs(schedule_storage_dir, 0755)

    if not os.path.exists(schedule_symlink_dir):
        os.symlink(schedule_storage_dir, schedule_symlink_dir)

    return filepath


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


def render_page(url_to_render, screenshot_filepath):
    with open(os.devnull, 'w') as devnull:
        retcode = subprocess.call(
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
        return retcode


def render_finished(screenshot_filepath, retcode):
    if retcode == 0:
        logging.info('Rendering %s successful', screenshot_filepath)
    elif retcode == 2:
        logging.error('Rendering %s timed out', screenshot_filepath)
    else:
        logging.error('Rendering %s failed (returned %d)',
                screenshot_filepath, retcode)


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

    logging.info('Rendering %s started', screenshot_filepath)
    _RENDER_POOL.apply_async(render_page,
            (url_to_render, screenshot_filepath),
            callback=functools.partial(render_finished, screenshot_filepath))


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

# This is intentionally at the bottom of the file. Specifically, it *must* be
# after the definition of render_page
#
# See: http://stackoverflow.com/a/2783017/303911
_RENDER_POOL = multiprocessing.Pool(processes=4)
