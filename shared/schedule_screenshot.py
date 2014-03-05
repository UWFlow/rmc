import calendar
import datetime
import hashlib
import logging
import os

import rmc.shared.constants as c
import rmc.models as m
import rmc.shared.tasks as tasks


# Bump this when old screenshots need to be invalidated and new ones created.
# After deploying, go to https://uwflow.com/admin/backfill_schedules to kick
# off a backfill for all users.
_VERSION_TAG = 'v1'


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
    return "static/schedules/%s-%s.png" % (_VERSION_TAG, stable_id)


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

    if best_week_date:
        return best_week_date
    else:
        logging.error("Can't find a best screenshot date for %s", user.id)
        return term_start_mon


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

    tasks.render_schedule_screenshot.delay(url_to_render, screenshot_filepath)


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
