import logging

import bson
import flask

import rmc.models as m
import rmc.server.view_helpers as view_helpers
import rmc.shared.rmclogger as rmclogger
import rmc.shared.util as util


def get_schedule_item_dicts(course_ids):
    # XXX(mack): revert
    #schedule_item_objs = m.ScheduleItem.objects(
    #        id__in=current_user.schedule_items)
    schedule_item_objs = m.ScheduleItem.objects(course_id__in=course_ids)
    return [si.to_dict() for si in schedule_item_objs]


def render_schedule_page(profile_user_id):
    # Fetch exam schedules and schedule items
    current_term_id = util.get_current_term_id()
    # XXX(mack): revert
    current_term_id = '2012_09'

    profile_user = m.User.objects.with_id(profile_user_id)
    profile_dict = profile_user.to_dict()
    profile_dict.update({
        'last_program_year_id': profile_user.get_latest_program_year_id(),
    })

    current_ucs = m.UserCourse.objects(user_id=profile_user_id, term_id=current_term_id)
    current_course_ids = [uc['course_id'] for uc in current_ucs]
    schedule_item_dicts = get_schedule_item_dicts(current_course_ids)

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
    )


def render_profile_page(profile_user_id):
    # TODO(mack): for dict maps, use .update() rather than overwriting to
    # avoid subtle overwrites by data that has fields filled out

    LAST_TERM_ID = util.get_current_term_id()

    # PART ONE - VALIDATION

    current_user = view_helpers.get_current_user()

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
        if not (profile_user_id in current_user.friend_ids
                or current_user.is_admin and flask.request.values.get('admin')):
            logging.warn("User (%s) tried to access non-friend profile (%s)"
                    % (current_user.id, profile_user_id))
            return view_helpers.redirect_to_profile(current_user)

        profile_user = m.User.objects.with_id(profile_user_id)
        # Technically we don't need this check due to above (under normal
        # operation). Though have this anyway as a failsafe
        if profile_user is None:
            logging.warn('profile_user is None')
            return view_helpers.redirect_to_profile(current_user)

    # Redirect the user appropriately... to /onboarding if they have no course
    # history, and to wherever they logged in from if they just logged in
    # TODO(david): Should have frontend decide whether to take us to /profile
    #     or /onboarding and not redirect in one of these two places
    if own_profile:
        redirect_url = flask.request.values.get('next')

        referrer = flask.request.referrer

        # TODO(david): Hardcoded for YC demo
        if current_user.email == 'davidhu91@gmail.com' and (referrer ==
                "http://uwflow.com/" or referrer == "http://localhost:5000/"):
            return flask.make_response(flask.redirect('onboarding'))

        if current_user.has_course_history and redirect_url:
            return flask.make_response(flask.redirect(redirect_url))
        elif not current_user.has_course_history:
            return flask.make_response(flask.redirect('onboarding'))

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
    friends = m.User.objects(id__in=profile_user.friend_ids).only(
            'id', 'fbid', 'first_name', 'last_name')

    # Fetch all professors for all courses
    professor_objs = m.Professor.get_reduced_professors_for_courses(
            transcript_courses)

    # PART THREE - TRANSFORM DATA TO DICTS

    # Convert professors to dicts
    professor_dicts = {}
    for professor_obj in professor_objs:
        professor_dicts[professor_obj['id']] = professor_obj

    # Convert courses to dicts
    course_dict_list, user_course_dict_list = m.Course.get_course_and_user_course_dicts(
        transcript_courses, current_user, include_friends=own_profile)
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
        user_dict = friend.to_dict()

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
            transcript_by_term.setdefault(uc_dict['term_id'], []).append(uc_dict)

        ordered_transcript = []
        for term_id, uc_dicts in sorted(transcript_by_term.items(), reverse=True):
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

    exam_objs = m.Exam.objects(course_id__in=current_course_ids)
    exam_dicts =  [e.to_dict() for e in exam_objs]

    # TODO(mack): use get_schedule_item_dicts()
    schedule_item_objs = m.ScheduleItem.objects(
            id__in=current_user.schedule_items)
    schedule_item_dicts = [si.to_dict() for si in schedule_item_objs]

    rmclogger.log_event(
        rmclogger.LOG_CATEGORY_IMPRESSION,
        rmclogger.LOG_EVENT_PROFILE, {
            'current_user': current_user.id,
            'profile_user': profile_user.id,
        },
    )

    return flask.render_template('profile_page.html',
        page_script='profile_page.js',
        transcript_obj=ordered_transcript,
        user_objs=user_dicts.values(),
        user_course_objs=user_course_dicts.values(),
        course_objs=course_dicts.values(),
        professor_objs=professor_dicts.values(),
        # TODO(mack): currently needed by jinja to do server-side rendering
        # figure out a cleaner way to do this w/o passing another param
        profile_obj=profile_dict,
        profile_user_id=profile_user.id,
        current_user_id=current_user.id,
        own_profile=own_profile,
        has_courses=current_user.has_course_history,
        exam_objs=exam_dicts,
        schedule_item_objs=schedule_item_dicts,
        has_shortlisted=current_user.has_shortlisted,
    )
