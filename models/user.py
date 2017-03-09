import random
import hashlib
from urllib import urlopen




from string import letters
from google.appengine.ext import db
from google.appengine.api import images


##### user stuff
def make_salt(length = 5):
    return ''.join(random.choice(letters) for x in xrange(length))

def make_pw_hash(name, pw, salt = None):
    if not salt:
        salt = make_salt()
    h = hashlib.sha256(name + pw + salt).hexdigest()
    return '%s,%s' % (salt, h)


class User(db.Model):
    username = db.StringProperty(required=True)
    first_name = db.StringProperty(required=True)
    last_name = db.StringProperty(required=True)
    pw_hash = db.StringProperty(required=True)
    email = db.StringProperty()
    avatar_image = db.BlobProperty()
    bio = db.TextProperty()


    @classmethod
    def create_sample_users(cls):
        pw = make_pw_hash("User1", "pass")
        user = User.register("User1", "John", "Smith", pw, "John@email.com")

        url = 'http://e0.365dm.com/13/09/800x600/Chelsea-v-Basel-Frank-Lampard_3005627.jpg?20131107160649'
        response = urlopen(url)
        img = response.read()
        avatar_image = images.resize(img, 150, 150, crop_to_fit=True)

        user.avatar_image = avatar_image
        user.put()

    @classmethod 
    def username_in_use(cls, username):
        return User.gql("WHERE username = '%s'" % username).get()


    @classmethod
    def register(cls, username, first_name, last_name, pw,
                 email = None, avatar_image=None):

        pw_hash = make_pw_hash(username, pw)
        return User(username = username,
                    first_name=first_name,
                    last_name=last_name,
                    pw_hash = pw_hash,
                    email = email)


    def valid_pw(self, username, pw):
        salt = self.pw_hash.split(',')[0]
        return self.pw_hash == make_pw_hash(username, pw, salt)


    @classmethod
    def login(cls, username, pw):
        u = User.gql("WHERE username='%s'" % username).get()
        if u and u.valid_pw(username, pw):
            return u

    
