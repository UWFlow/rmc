import rmc.models as m
import rmc.shared.constants as c

import mongoengine as me


def normalize_user_course_ratings():
    """Normalize user course ratings to be 0/1 for Yes/No. Before it was
    0.2,0.4,0.6,0.8.1.0 OR possible 0.0,0.25,0.5,0.75,1.0"""

    num_changes = [0]

    def normalize(value):
        # Ranges to ignore are 0.5 to 0.6, add some epsilon just to be
        # safe against float rounding
        if value is None:
            new_value = None
        elif value < 0.45:
            new_value = 0.0
        elif value > 0.65:
            new_value = 1.0
        else:
            new_value = None

        if new_value != value:
            num_changes[0] += 1

        return new_value

    for uc in m.UserCourse.objects:
        if not m.Course.objects.with_id(uc.course_id):
            print 'Skipping course %s' % uc.course_id
            continue

        cr = uc.course_review
        pr = uc.professor_review

        cr.interest = normalize(cr.interest)
        cr.easiness = normalize(cr.easiness)
        cr.usefulness = normalize(cr.usefulness)

        pr.clarity = normalize(pr.clarity)
        pr.passion = normalize(pr.passion)

        uc.save()

    print 'Updated %d reviews' % num_changes[0]


if __name__ == '__main__':
    me.connect(c.MONGO_DB_RMC)

    normalize_user_course_ratings()
