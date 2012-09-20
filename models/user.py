from mongoengine import Document
import _field as f

class User(Document):
    meta = {
        'indexes': [
            'fb_access_token',
            'fbid',
        ],
    }

    # id = f.ObjectIdField(primary_key=True)

    # eg. Mack (can include middle name)
    first_name = f.StringField(required=True)

    # eg. Duan
    last_name = f.StringField(required=True)

    # eg. 1647810326
    fbid = f.IntField(required=True, unique=True)

    # http://stackoverflow.com/questions/4408945/what-is-the-length-of-the-access-token-in-facebook-oauth2
    fb_access_token = f.StringField(max_length=255, required=True, unique=True)

    email = f.EmailField()

    # eg. list of user objectids
    friend_ids = f.ListField(f.ObjectIdField())

    birth_date = f.DateTimeField()

    last_login_time = f.DateTimeField()
    # TODO(mack): consider using SequenceField()
    num_visits = f.IntField(min_value=0, default=0)

    # eg. mduan or 20345619 ?
    student_id = f.StringField()
    # eg. university_of_waterloo ?
    school_id = f.StringField()
    # eg. software_engineering ?
    program_id = f.StringField()


    @property
    def name(self):
        return '%s %s' % (self.first_name , self.last_name)
