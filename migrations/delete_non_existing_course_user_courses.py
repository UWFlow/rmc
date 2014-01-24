import rmc.models as m
import rmc.shared.constants as c

import mongoengine as me


def delete_non_existing_course_user_courses():
    """
    NOTE: Do not run this yet, as it seems from dry run that there are
    some usercourses that we would be deleting that are legit courses
    that we should try getting into our Course collection.

    Delete UserCourse models that reference Course objects we dont' have
    (e.g. wkrpt100)"""

    for uc in m.UserCourse.objects:
        if not m.Course.objects.with_id(uc.course_id):
            print 'deleting: %s, %s, %s' % (
                    uc.user_id, uc.course_id, uc.term_id)
            uc.delete()


if __name__ == '__main__':
    me.connect(c.MONGO_DB_RMC)

    delete_non_existing_course_user_courses()
