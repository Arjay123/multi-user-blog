import os
import jinja2
import webapp2
import re
import hmac
import random
import hashlib

from models.user import User
from models.post import Post
from string import letters
from google.appengine.ext import db
from google.appengine.api import images


template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), 
                               autoescape=True)

secret = "imsosecret"
USER_COOKIE_KEY = "user"


def render_str(template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)

"""
Base class for page handlers, contains common methods
needed by any handler
"""
class Handler(webapp2.RequestHandler):


    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)


    """ 
    before rendering the template, gets stored user object
    and passes to page params
    """
    def render_str(self, template, **params):
        params['user'] = self.user
        return render_str(template, **params)


    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))


    """
    create cookie value by hashing value w/ secret key
    return: value and hashed value in the form '%s|%s'
    """
    def make_secure_val(self, val):
        return '%s|%s' % (val, hmac.new(secret, val).hexdigest())


    """
    check cookie value w/ hash value to ensure it hasn't been modified by
    the requesting user

    return: cookie value if valid, else None
    """
    def check_secure_val(self, secure_val):
        val = secure_val.split('|')[0]
        if secure_val == self.make_secure_val(val):
            return val

    """
    sets cookie value
    """
    def set_cookie(self, name, value):
        h = self.make_secure_val(value)
        self.response.headers.add_header('Set-Cookie', 
                '%s=%s; Path=/' % (name, str(h)))

    """
    gets valid cookie value
    """
    def get_cookie(self, name):
        cookie_val = self.request.cookies.get(name)
        return cookie_val and self.check_secure_val(cookie_val)


    """
    called before loading page, if user is logged in, gets user from db
    using the id stored in USER_COOKIE_KEY cookie
    """
    def initialize(self, *a, **kw):
        webapp2.RequestHandler.initialize(self, *a, **kw)
        uid = self.get_cookie(USER_COOKIE_KEY)
        self.user = uid and User.get_by_id(int(uid))


"""
Handler base class for any pages that edit the User object in the db
"""
class UserSettingsHandler(Handler):

    USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
    def valid_username(self, username):
        return username and self.USER_RE.match(username)

    PASS_RE = re.compile(r"^.{3,20}$")
    def valid_password(self, password):
        return password and self.PASS_RE.match(password)

    EMAIL_RE  = re.compile(r'^[\S]+@[\S]+\.[\S]+$')
    def valid_email(self, email):
        return not email or self.EMAIL_RE.match(email)


"""
Settings page, user can change some of their information from here
"""
class UserPage(UserSettingsHandler):
    def get(self):
        self.render("user.html")
        

"""
New user signup page
"""
class SignupPage(UserSettingsHandler):
    def get(self):

        # this page is not accessible by a logged in user
        if self.user:
            self.redirect("/blog.html")
            return

        self.render("signup.html")

    def post(self):

        # get submitted values
        if self.request.get("frm_submit") == "login":
            pass
        else:

            username = self.request.get("username")
            first_name = self.request.get("first_name")
            last_name = self.request.get("last_name")
            password = self.request.get("password")
            confirm_pw = self.request.get("confirm_pw")
            email = self.request.get("email")

            valid = True
            username_error = ""
            first_name_error = ""
            last_name_error = ""
            password_error = ""
            confirm_pw_error = ""
            email_error = ""

            retry_params = { "username": username,
                             "first_name": first_name,
                             "last_name": last_name,
                             "email": email,
                             "signup": True
                            }

            # check if all submitted params are valid
            if not self.valid_username(username):
                valid = False
                retry_params["username_error"] = "Username is invalid"

            if not first_name:
                valid = False
                retry_params["first_name_error"] = "Please enter a first name"

            if not last_name:
                valid = False
                retry_params["last_name_error"] = "Please enter a last name"

            if not self.valid_password(password):
                valid = False
                retry_params["password_error"] = "Password is invalid"
            elif password != confirm_pw:
                valid = False
                retry_params["confirm_pw_error"] = "Passwords do not match"

            if not self.valid_email(email):
                valid = False
                retry_params["email_error"] = "Email is invalid"
            
            # if any params invalid, reload signup page w/ previous values
            if not valid:
                self.render("signup.html", **retry_params)

            else:

                # check if username used, reload signup page
                if User.username_in_use(username):
                    retry_params["username_error"] = "Username in use"
                    self.render("signup.html", **retry_params)
                    print(User.username_in_use(username))
                    return


                user = User.register(username, 
                                     first_name, 
                                     last_name, 
                                     password, 
                                     email)

                avatar_image = self.request.get("img")
                if avatar_image:
                    avatar_image = images.resize(avatar_image, 150, 150)
                    user.avatar_image = avatar_image

                user.put()

                self.set_cookie(USER_COOKIE_KEY, str(user.key().id()))
                self.redirect("/")

"""
Handler for rendering user avatar images stored as BlobProperty values
"""
class UserImageHandler(Handler):
    def get(self):
        img_id = self.request.get("img_id")
        if img_id and img_id.isdigit():

            user = User.get_by_id(int(img_id))
            
            if user and user.avatar_image:
                self.response.headers["Content-Type"] = "image/jpeg"
                self.response.out.write(user.avatar_image)

"""
Handler for rendering post header images stored as BlobProperty values
"""
class PostImageHandler(Handler):
    def get(self):
        img_id = self.request.get("img_id")
        if img_id and img_id.isdigit():

            post = Post.get_by_id(int(img_id))
            
            if post and post.header_image:
                self.response.headers["Content-Type"] = "image/jpeg"
                self.response.out.write(post.header_image)

"""
Home page handler
"""
class MainPage(Handler):
    def get(self):
        posts = Post.all().order('-created')
        self.render("blog.html", posts=posts)


"""
Handler for new post submissions
"""
class NewPostPage(Handler):
    def get(self):
        self.render("newpost.html")


    def post(self):
        title = self.request.get("title")
        content = self.request.get("content")

        header_image = self.request.get("img")
        header_image = images.resize(header_image, 500, 200)

        post = Post(title=title, content=content)
        post.header_image = header_image
        post.put()



app = webapp2.WSGIApplication([('/', MainPage),
                               ('/newpost', NewPostPage),
                               ('/postimg', PostImageHandler),
                               ('/userimg', UserImageHandler),
                               ('/signup', SignupPage),
                               ('/user', UserPage)])