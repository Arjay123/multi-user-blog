import hashlib
import random
from google.appengine.api import images
from google.appengine.ext import db
from string import letters

##### user stuff
def make_salt(length = 5):
    return ''.join(random.choice(letters) for x in xrange(length))

def make_pw_hash(name, pw, salt = None):
    if not salt:
        salt = make_salt()
    h = hashlib.sha256(name + pw + salt).hexdigest()
    return '%s,%s' % (salt, h)


class User(db.Model):
    """ A User object that can interact with the site
    
    User object containing information about the user and allows
    the user to create blog posts and post comments.

    Attributes:
        username - username used to log in
        first_name - first name
        last_name - last name
        pw_hash - hashed password and salt separatated by |
        email - email
        avatar_image - actual image file of user's avatar
        bio - short biography of user
    """
    username = db.StringProperty(required=True)
    first_name = db.StringProperty(required=True)
    last_name = db.StringProperty(required=True)
    pw_hash = db.StringProperty(required=True)
    email = db.StringProperty()
    avatar_image = db.BlobProperty()
    bio = db.TextProperty()


    @classmethod 
    def username_in_use(cls, username):
        """ Checks if username is already being used

        Returns:
            None or user entity that uses the username
        """
        return User.gql("WHERE username = '%s'" % username).get()


    @classmethod
    def register(cls, username, first_name, last_name, pw,
                 email = None, avatar_image=None):
        """ Creates a user object w/ hashed pw

        """
        pw_hash = make_pw_hash(username, pw)
        return User(username = username,
                    first_name=first_name,
                    last_name=last_name,
                    pw_hash = pw_hash,
                    email = email)


    def get_full_name(self):
        """ Returns first + last name concatenated

        """
        return self.first_name + " " + self.last_name


    def get_formatted_bio(self):
        """ Returns biography formatted for html

        """
        if self.bio:
            return self.bio.replace("\n", "<br>")

    

    def valid_pw(self, username, pw):
        """ Check against pw_hash if login password is correct
        
        Return:
            Bool value whether pw is correct or not
        """
        salt = self.pw_hash.split(',')[0]
        return self.pw_hash == make_pw_hash(username, pw, salt)


    @classmethod
    def login(cls, username, pw):
        """ Logs in user
        
        Checks if username and password are valid

        Return:
            User entity if crendentials match
        """
        u = User.gql("WHERE username='%s'" % username).get()
        if u and u.valid_pw(username, pw):
            return u

    
