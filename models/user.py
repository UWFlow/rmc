import mongoengine as me

class User(me.Document):
    meta = {
        'indexes': [
            'fb_access_token',
            'fbid',
        ],
    }

    # id = me.ObjectIdField(primary_key=True)

    # eg. Mack (can include middle name)
    first_name = me.StringField(required=True)

    # eg. Duan
    last_name = me.StringField(required=True)

    # eg. 1647810326
    fbid = me.IntField(required=True, unique=True)

    # http://stackoverflow.com/questions/4408945/what-is-the-length-of-the-access-token-in-facebook-oauth2
    fb_access_token = me.StringField(max_length=255, required=True, unique=True)

    email = me.EmailField()

    # eg. list of user objectids
    friend_ids = me.ListField(me.ObjectIdField())

    birth_date = me.DateTimeField()

    last_login_time = me.DateTimeField()
    # TODO(mack): consider using SequenceField()
    num_visits = me.IntField(min_value=0, default=0)

    # eg. mduan or 20345619 ?
    student_id = me.StringField()
    # eg. university_of_waterloo ?
    school_id = me.StringField()
    # eg. software_engineering ?
    program_id = me.StringField()


    @property
    def name(self):
        return '%s %s' % (self.first_name , self.last_name)
