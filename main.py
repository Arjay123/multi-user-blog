import os
import jinja2
import webapp2
import re
import hmac
import random
import hashlib

from models.user import User
from string import letters
from google.appengine.ext import db
from google.appengine.api import images


template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), 
                               autoescape=True)

secret = "imsosecret"


USER_COOKIE_KEY = "user"

class Handler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))

    def make_secure_val(self, val):
        return '%s|%s' % (val, hmac.new(secret, val).hexdigest())

    def check_secure_val(self, secure_val):
        val = secure_val.split('|')[0]
        if secure_val == self.make_secure_val(val):
            return val

    def set_cookie(self, name, value):
        h = self.make_secure_val(value)
        self.response.headers.add_header('Set-Cookie', 
                '%s=%s; Path=/' % (name, str(h)))

    def get_cookie(self, name):
        cookie_val = self.request.cookies.get(name)
        return cookie_val and self.check_secure_val(cookie_val)





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




class Post(db.Model):
    title = db.StringProperty(required=True)
    content = db.TextProperty(required=True)
    header_image = db.BlobProperty()
    created = db.DateTimeProperty(auto_now_add=True)




class UserPage(UserSettingsHandler):
    def get(self):
        user_id = self.get_cookie(USER_COOKIE_KEY)
        if user_id:
            user = User.get_by_id(int(user_id))
            self.render("user.html", user=user)
        

class SignupPage(UserSettingsHandler):
    def get(self):
        self.render("signup.html")

    def post(self):
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
                         "email": email }

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
        

        if not valid:
            self.render("signup.html", **retry_params)

        else:

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


class UserImageHandler(Handler):
    def get(self):
        img_id = self.request.get("img_id")
        if img_id and img_id.isdigit():

            user = User.get_by_id(int(img_id))
            

            if user and user.avatar_image:
                self.response.headers["Content-Type"] = "image/jpeg"
                self.response.out.write(user.avatar_image)
            else:
                print "poopoo"

        else:
            print "poop"

class ImageHandler(Handler):
    def get(self):
        img_id = self.request.get("img_id")
        if img_id and img_id.isdigit():

            post = Post.get_by_id(int(img_id))
            

            if post and post.header_image:
                self.response.headers["Content-Type"] = "image/jpeg"
                self.response.out.write(post.header_image)
            else:
                print "poopoo"

        else:
            print "poop"

class MainPage(Handler):
    def get(self):
        posts_cursor = Post.gql("ORDER BY created DESC")
        posts = posts_cursor.fetch(limit=10)
        self.render("blog.html", posts=posts)

class NewPostPage(Handler):
    def get(self):
        self.render("newpost.html")

    def post(self):
        title = self.request.get("title")
        content = self.request.get("content")

        header_image = self.request.get("img")
        header_image = images.resize(header_image, 500, 200)

        valid = True

        post = Post(title=title, content=content)
        post.header_image = header_image
        post.put()



app = webapp2.WSGIApplication([('/', MainPage),
                               ('/newpost', NewPostPage),
                               ('/img', ImageHandler),
                               ('/userimg', UserImageHandler),
                               ('/signup', SignupPage),
                               ('/user', UserPage)])