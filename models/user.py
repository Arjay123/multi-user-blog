import hashlib
import random
from google.appengine.api import images
from google.appengine.ext import db
from string import letters


def make_salt(length = 5):
    """ Creates salt from random letters

    Args:
        length - length of salt string

    Returns:
        salt string
    """
    return ''.join(random.choice(letters) for x in xrange(length))


def make_pw_hash(name, pw, salt = None):
    """ creates hashed pw and salt string 
    
    Args:
        name - username
        pw - password
        salt - previous salt, used for checking valid pw instead of creating
    """
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
        pw_hash - hashed password and salt separatated by ,
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


    def change_user_settings(self, 
                             first_name=None, 
                             last_name=None,
                             password=None, 
                             email=None, 
                             img=None, 
                             bio=None):

        if first_name:
            self.first_name = first_name

        if last_name:
            self.last_name = last_name

        if password:
            self.change_password(password)

        if email:
            self.email = email

        if img:
            self.change_user_image(img)

        if bio:
            self.bio = bio

        self.put()


    def change_user_image(self, img):
        print "change image"
        avatar_image = images.resize(img, 150, 150, crop_to_fit=True)
        self.avatar_image = avatar_image


    def change_password(self, new_pw):
        self.pw_hash = make_pw_hash(self.username, new_pw)


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




    
