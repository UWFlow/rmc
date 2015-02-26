from datetime import datetime
import logging

import bson
import flask
import icalendar
import pytz

import rmc.models as m
import rmc.server.view_helpers as view_helpers
import rmc.shared.rmclogger as rmclogger
import rmc.shared.util as util
import rmc.shared.schedule_screenshot as schedule_screenshot


# Local constants
RESHOW_ONBOARDING_DELAY_DAYS = 45
RESHOW_SCHEDULE_DELAY_DAYS = 5


def render_schedule_page(profile_user):
    profile_dict = profile_user.to_dict()
    profile_dict.update({
        'last_program_year_id': profile_user.get_latest_program_year_id(),
    })

    # TODO(david): Show exam slots here as well (see render_profile_page)
    schedule_item_dicts = profile_user.get_schedule_item_dicts()

    course_ids = [si['course_id'] for si in schedule_item_dicts]
    courses = m.Course.objects(id__in=course_ids)
    course_dicts = [c.to_dict() for c in courses]

    current_user = view_helpers.get_current_user()
    current_user_id = None
    if current_user:
        current_user_id = current_user.id

    rmclogger.log_event(
        rmclogger.LOG_CATEGORY_IMPRESSION,
        rmclogger.LOG_EVENT_SCHEDULE_VIEW, {
            'current_user': current_user_id,
            'profile_user': profile_user.id,
        },
    )

    user_dicts = [profile_dict]
    if current_user and current_user_id != profile_user.id:
        user_dicts.append(current_user.to_dict())

    return flask.render_template('schedule_page.html',
        page_script='schedule_page.js',
        profile_obj=profile_dict,
        user_objs=user_dicts,
        profile_user_id=profile_user.id,
        current_user_id=current_user_id,
        schedule_item_objs=schedule_item_dicts,
        course_objs=course_dicts,
        show_printable=flask.request.values.get('print'),
    )


def render_schedule_ical_feed(profile_user_secret_id):
    profile_user = (m.User.objects(secret_id=profile_user_secret_id.upper())
                        .first())

    if profile_user is None:
        logging.error("No profile user with secret id '%s'" %
            profile_user_secret_id)
        return ''

    exams = profile_user.get_current_term_exams()
    schedule_item_dict_list = profile_user.get_schedule_item_dicts(
                                    exam_objs=exams)

    course_ids = set([sid['course_id'] for sid in schedule_item_dict_list])

    limited_course_list = (m.Course.objects(id__in=course_ids)
        .only('id', 'department_id', 'number', 'name'))

    humanized_course_id = {}

    for limited_course in limited_course_list:
        humanized_course_id[limited_course.id] = (
            limited_course.department_id.upper() + ' ' +
            limited_course.number
        )

    course_name_map = {c['id']: c['name'] for c in limited_course_list}

    cal = icalendar.Calendar()
    cal.add('x-wr-calname', 'uwflow.com schedule')
    cal.add('x-wr-caldesc', 'Schedule exported from https://uwflow.com')

    for schedule_item_dict in schedule_item_dict_list:
        event = icalendar.Event()
        course_id = schedule_item_dict['course_id']
        summary_fmt = ('%(course_id)s - %(section_type)s %(section_num)s'
                ' - %(course_name)s')
        summary = summary_fmt % {
            'course_id': humanized_course_id.get(course_id, course_id),
            'section_type': schedule_item_dict['section_type'],
            'section_num': schedule_item_dict['section_num'],
            'course_name': course_name_map.get(course_id, ''),
        }
        event.add('summary', summary)

        # We need to make sure we explicitly specify a timezone in the
        # datetimes we emit to the ICS file, otherwise, some calendars (eg.
        # Calendar.app) will interpret the time as local time (instead of UTC,
        # which is what we store our datetime as).
        to_utc = pytz.utc.localize

        # TODO(jlfwong): DTSTAMP is actually supposed to be when the event was
        # created, not when it is. Not sure what to put here
        event.add('dtstamp', to_utc(schedule_item_dict['start_date']))
        event.add('dtstart', to_utc(schedule_item_dict['start_date']))
        event.add('dtend', to_utc(schedule_item_dict['end_date']))

        # TODO(david): There should be a method on a ScheduleItem to return
        #     a location string, except we have this stupid pattern of
        #     returning dicts from functions instead of objects.
        event.add('location', '%s %s' % (schedule_item_dict['building'],
                schedule_item_dict['room']))

        cal.add_component(event)

    response = flask.make_response(cal.to_ical())
    response.headers["Content-type"] = "text/calendar"
    return response


def render_profile_page(profile_user_id, current_user=None):
    # TODO(mack): for dict maps, use .update() rather than overwriting to
    # avoid subtle overwrites by data that has fields filled out

    LAST_TERM_ID = util.get_current_term_id()

    # PART ONE - VALIDATION

    current_user = current_user or view_helpers.get_current_user()

    try:
        if profile_user_id:
            profile_user_id = bson.ObjectId(profile_user_id)
    except:
        logging.warn('Invalid profile_user_id (%s)' % profile_user_id)
        return view_helpers.redirect_to_profile(current_user)

    if not profile_user_id:
        return view_helpers.redirect_to_profile(current_user)

    if profile_user_id == current_user.id:
        own_profile = True
        profile_user = current_user
    else:
        own_profile = False

        # Allow only friends to view profile
        if not (profile_user_id in current_user.friend_ids or (
                current_user.is_admin and flask.request.values.get('admin'))):
            logging.info("User (%s) tried to access non-friend profile (%s)"
                    % (current_user.id, profile_user_id))
            return view_helpers.redirect_to_profile(current_user)

        profile_user = m.User.objects.with_id(profile_user_id)
        # Technically we don't need this check due to above (under normal
        # operation). Though have this anyway as a failsafe
        if profile_user is None:
            logging.warn('profile_user is None')
            return view_helpers.redirect_to_profile(current_user)

    if own_profile:
        profile_user_secret_id = profile_user.get_secret_id()
    else:
        profile_user_secret_id = None

    show_import_schedule = False
    # Redirect the user appropriately... to /onboarding if they have no course
    # history, and to wherever they logged in from if they just logged in
    # TODO(david): Should have frontend decide whether to take us to /profile
    #     or /onboarding and not redirect in one of these two places
    if own_profile:
        redirect_url = flask.request.values.get('next')

        show_onboarding = False
        if not current_user.has_course_history:
            if not current_user.last_show_onboarding:
                show_onboarding = True
            else:
                time_delta = datetime.now() - current_user.last_show_onboarding
                # If they haven't imported any courses yet and the last time
                # the user was on the onboarding page is more than 5 days ago,
                # show the onboarding page again
                if time_delta.days > RESHOW_ONBOARDING_DELAY_DAYS:
                    show_onboarding = True

        # See https://uwflow.uservoice.com/admin/tickets/62
        if profile_user_id == '50b8ce2cd89d62310645ca78':
            show_onboarding = False

        if show_onboarding:
            onboarding_url = '/onboarding'
            if flask.request.query_string:
                onboarding_url = '%s?%s' % (
                        onboarding_url, flask.request.query_string)
            return flask.make_response(flask.redirect(onboarding_url))
        else:
            redirect_url = flask.request.values.get('next')
            if redirect_url:
                return flask.make_response(flask.redirect(redirect_url))

        # Show the import schedule view if it's been long enough
        if not current_user.has_schedule:
            if current_user.last_show_import_schedule:
                time_delta = (datetime.now() -
                              current_user.last_show_import_schedule)
                # User didn't import schedule yet, reshow every few days
                if time_delta.days > RESHOW_SCHEDULE_DELAY_DAYS:
                    show_import_schedule = True
            else:
                show_import_schedule = True

            if show_import_schedule:
                # TODO(Sandy): Do this on modal dismiss instead
                current_user.last_show_import_schedule = datetime.now()
                current_user.save()

    # PART TWO - DATA FETCHING

    # Get the mutual course ids of friends of profile user
    mutual_course_ids_by_friend = {}
    if own_profile:
        mutual_course_ids_by_friend = profile_user.get_mutual_course_ids(
            view_helpers.get_redis_instance())

    def get_friend_course_ids_in_term(friend_ids, term_id):
        user_courses = m.UserCourse.objects(
                term_id=term_id, user_id__in=friend_ids).only(
                    'user_id', 'course_id')

        last_term_course_ids_by_friend = {}
        for uc in user_courses:
            last_term_course_ids_by_friend.setdefault(
                    uc.user_id, []).append(uc.course_id)
        return last_term_course_ids_by_friend

    # Get the course ids of last term courses of friends of profile user
    last_term_course_ids_by_friend = get_friend_course_ids_in_term(
            profile_user.friend_ids, LAST_TERM_ID)

    # Get the course ids of courses profile user has taken
    profile_course_ids = set(profile_user.course_ids)

    # Fetch courses for transcript, which need more detailed information
    # than other courses (such as mutual and last term courses for friends)
    transcript_courses = list(m.Course.objects(id__in=profile_course_ids))

    # Fetch remainining courses that need less data. This will be mutual
    # and last term courses for profile user's friends
    friend_course_ids = set()
    friend_courses = []
    if own_profile:
        for course_ids in mutual_course_ids_by_friend.values():
            friend_course_ids = friend_course_ids.union(course_ids)
        for course_ids in last_term_course_ids_by_friend.values():
            friend_course_ids = friend_course_ids.union(course_ids)
        friend_course_ids = friend_course_ids - profile_course_ids
        friend_courses = m.Course.objects(
                id__in=friend_course_ids).only('id', 'name')

    # Fetch simplified information for friends of profile user
    # (for friend sidebar)
    friends = profile_user.get_friends()

    # Fetch all professors for all courses
    professor_objs = m.Professor.get_reduced_professors_for_courses(
            transcript_courses)

    # PART THREE - TRANSFORM DATA TO DICTS

    # Convert professors to dicts
    professor_dicts = {}
    for professor_obj in professor_objs:
        professor_dicts[professor_obj['id']] = professor_obj

    # Convert courses to dicts
    course_dict_list, user_course_dict_list, user_course_list = (
            m.Course.get_course_and_user_course_dicts(
                transcript_courses, current_user, include_friends=own_profile))
    course_dicts = {}
    for course_dict in course_dict_list:
        course_dicts[course_dict['id']] = course_dict
    user_course_dicts = {}
    for user_course_dict in user_course_dict_list:
        user_course_dicts[user_course_dict['id']] = user_course_dict

    profile_uc_dict_list = []

    # We only need to fetch usercourses for profile user if it is not the
    # current user since m.Course.get_course_and_user_course_dicts() will
    # have already fetched usercourses for the current user
    if not own_profile:
        # Get the user courses of profile user
        profile_uc_dict_list = [
                uc.to_dict() for uc in profile_user.get_user_courses()]
        # Get a mapping from course id to user_course for profile user
        profile_user_course_by_course = {}
        for uc_dict in profile_uc_dict_list:
            profile_user_course_by_course[uc_dict['course_id']] = uc_dict

    # Fill in with information about profile user
    for course in transcript_courses:
        course_dict = course_dicts[course.id]

        if not own_profile:
            # This has already been done for current user
            profile_uc_dict = profile_user_course_by_course.get(course.id)
            profile_user_course_id = profile_uc_dict['id']
            user_course_dicts[profile_user_course_id] = profile_uc_dict

            # Since we only fetched the user courses of the logged in user in
            # m.Course.get_course_and_user_course_dicts() above, gotta also
            # add the user courses of the profile user here
            user_course_dict_list.append(profile_uc_dict)
        else:
            profile_user_course_id = course_dict.get('user_course_id')
            if profile_user_course_id:
                profile_uc_dict_list.append(
                        user_course_dicts[profile_user_course_id])

        course_dict['profile_user_course_id'] = profile_user_course_id

    for course in friend_courses:
        course_dicts[course.id] = course.to_dict()

    def filter_course_ids(course_ids):
        return [course_id for course_id in course_ids
                if course_id in course_dicts]

    # Convert friend users to dicts
    user_dicts = {}
    # TODO(mack): should really be named current_term
    last_term = m.Term(id=LAST_TERM_ID)
    for friend in friends:
        user_dict = friend.to_dict(extended=False)

        if own_profile:
            user_dict.update({
                'last_term_name': last_term.name,
                'last_term_course_ids': filter_course_ids(
                    last_term_course_ids_by_friend.get(friend.id, [])),
                'mutual_course_ids': filter_course_ids(
                    mutual_course_ids_by_friend.get(friend.id, [])),
            })

        user_dicts[friend.id] = user_dict

    # Convert profile user to dict
    # TODO(mack): This must be after friend user dicts since it can override
    # data in it. Remove this restriction
    profile_dict = profile_user.to_dict(include_course_ids=True)
    profile_dict.update({
        'last_program_year_id': profile_user.get_latest_program_year_id(),
    })
    user_dicts.setdefault(profile_user.id, {}).update(profile_dict)

    # Convert current user to dict
    # TODO(mack): This must be after friend user dicts since it can override
    # data in it. Remove this restriction
    if not own_profile:
        user_dicts.setdefault(current_user.id, {}).update(
                current_user.to_dict(include_course_ids=True))

    def get_ordered_transcript(profile_uc_dict_list):
        transcript_by_term = {}

        for uc_dict in profile_uc_dict_list:
            (transcript_by_term.setdefault(uc_dict['term_id'], [])
                               .append(uc_dict))

        ordered_transcript = []
        for term_id, uc_dicts in sorted(transcript_by_term.items(),
                                        reverse=True):
            curr_term = m.Term(id=term_id)
            term_dict = {
                'id': curr_term.id,
                'name': curr_term.name,
                'program_year_id': uc_dicts[0].get('program_year_id'),
                'course_ids': [uc_dict['course_id'] for uc_dict in uc_dicts
                    if uc_dict['course_id'] in course_dicts],
            }
            ordered_transcript.append(term_dict)

        return ordered_transcript, transcript_by_term

    # Store courses by term as transcript using the current user's friends
    ordered_transcript, transcript_by_term = get_ordered_transcript(
            profile_uc_dict_list)

    # Fetch exam schedules and schedule items
    current_term_id = util.get_current_term_id()

    current_term_courses = transcript_by_term.get(current_term_id, [])
    current_course_ids = [c['course_id'] for c in current_term_courses]

    exam_objs = profile_user.get_current_term_exams(current_course_ids)
    exam_dicts = [e.to_dict() for e in exam_objs]
    exam_updated_date = None
    if exam_objs:
        exam_updated_date = exam_objs[0].id.generation_time

    # Set the course to prompt the user to review if it's time
    course_id_to_review = None
    if own_profile and profile_user.should_prompt_review():
        profile_user_courses = filter(lambda uc: uc.user_id == profile_user.id,
                user_course_list)
        uc_to_review = m.UserCourse.select_course_to_review(
                profile_user_courses)
        course_id_to_review = uc_to_review and uc_to_review.course_id

        if uc_to_review:
            uc_to_review.select_for_review(current_user)

    # NOTE: This implictly requires that the courses on the schedule are on the
    # transcript, since these course objects are needed by the schedule  on the
    # frontend. This should be the case since when we add a schedule item, a
    # corresponding item is added to the transcript.
    schedule_item_dicts = profile_user.get_schedule_item_dicts(exam_objs)
    failed_schedule_item_dicts = profile_user.get_failed_schedule_item_dicts()

    referrals = m.User.objects(referrer_id=current_user.id)
    referral_objs = [referral.to_dict() for referral in referrals]

    rmclogger.log_event(
        rmclogger.LOG_CATEGORY_IMPRESSION,
        rmclogger.LOG_EVENT_PROFILE, {
            'current_user': current_user.id,
            'profile_user': profile_user.id,
        },
    )

    schedule_screenshot.update_screenshot_async(profile_user)

    scholarships = m.Scholarship.objects()
    # Filter scholarships based on program
    closed_scholarship_ids_set = set(profile_user.closed_scholarship_ids)
    scholarships = [s for s in scholarships if profile_user.short_program_name
            in s.programs and s.id not in closed_scholarship_ids_set]
    scholarships_dict = [s.to_dict() for s in scholarships]

    return flask.render_template('profile_page.html',
        page_script='profile_page.js',
        transcript_obj=ordered_transcript,
        user_objs=user_dicts.values(),
        referral_objs=referral_objs,
        user_course_objs=user_course_dicts.values(),
        course_objs=course_dicts.values(),
        professor_objs=professor_dicts.values(),
        # TODO(mack): currently needed by jinja to do server-side rendering
        # figure out a cleaner way to do this w/o passing another param
        profile_obj=profile_dict,
        profile_user_id=profile_user.id,
        current_user_id=current_user.id,
        profile_user_secret_id=profile_user_secret_id,
        own_profile=own_profile,
        has_courses=profile_user.has_course_history,
        exam_objs=exam_dicts,
        exam_updated_date=exam_updated_date,
        schedule_item_objs=schedule_item_dicts,
        failed_schedule_item_objs=failed_schedule_item_dicts,
        has_shortlisted=profile_user.has_shortlisted,
        show_import_schedule=show_import_schedule,
        show_import_schedule_button=own_profile and (not
                profile_user.has_schedule),
        course_id_to_review=course_id_to_review,
        scholarship_objs=scholarships_dict,
    )
