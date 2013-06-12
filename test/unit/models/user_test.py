import datetime
import random
import string

import rmc.models as m
import rmc.test.lib as testlib

def gen_user(**kwargs):
    attrs = {
        'join_date'   : datetime.datetime.now(),
        'join_source' : m.User.JoinSource.FACEBOOK,
        'fb_access_token' : ''.join(random.choice(string.ascii_uppercase) for x in xrange(30)),
        'fb_access_token_expiry_date' :
            datetime.datetime.now() + datetime.timedelta(days=100)
    }

    attrs.update(kwargs)

    return m.User(**attrs)

class UserTest(testlib.ModelTestCase):

    def test_save_converts_friend_fbids_to_friend_ids(self):
        # TODO(jlfwong): Make something like Factory Girl to make sure that
        # generated instances are actually valid to stop these tests from
        # testing data scenarios that don't happen.
        # https://github.com/thoughtbot/factory_girl_rails
        friend1 = gen_user(fbid=u'12345', first_name='Winston', last_name='Bishop')
        friend1.save()
        friend2 = gen_user(fbid=u'54321', first_name='Nick', last_name='Miller')
        friend2.save()

        u = gen_user(fbid=u'65432', first_name='Jessica', last_name='Day', friend_fbids=[
            friend1.fbid,
            friend2.fbid
        ])
        u.save()

        self.assertEquals(u.friend_ids, [friend1.id, friend2.id])
