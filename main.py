import os
import jinja2
import webapp2
import re
import hmac
import random
import hashlib
import time

from models.user import User
from models.post import Post
from models.postphoto import PostPhoto
from string import letters
from google.appengine.ext import db
from google.appengine.ext import blobstore
from google.appengine.api import images

from google.appengine.ext.webapp import blobstore_handlers


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


    def login(self, uid):
        self.set_cookie(USER_COOKIE_KEY, uid)


    def logout(self):
        self.set_cookie(USER_COOKIE_KEY, "")
        self.user = None


    def is_logged_in(self):
        return self.user


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
List of posts created by current user
"""
class UserPostsPage(Handler):
    def get(self):
        posts = Post.gql("WHERE author_id='%s' ORDER BY created DESC" % 
            str(self.user.key().id()))
        self.render("post_list.html", posts=posts.fetch(limit=None))


"""
Edit post handler
"""
class EditPostPage(Handler):
    def get(self, post_id):
        if post_id:
            post = Post.get_by_id(int(post_id))
            self.render("editpost.html", post=post)


    def post(self, post_id):
        if post_id:
            post = Post.get_by_id(int(post_id))

            new_title = self.request.get("title")
            new_content = self.request.get("content")
            new_header_image = self.request.get("img")
            submit = False

            if new_title:
                submit=True
                post.title = new_title


            if new_content:
                submit=True
                post.content = new_content

            if new_header_image:
                submit=True
                
                # delete images


                # insert new images
                header_image_thumb = images.resize(new_header_image, 
                                           height=200)

                header_image_small = images.resize(new_header_image, 
                                                   width=500, 
                                                   height=200, 
                                                   crop_to_fit=True)

                header_image_med = images.resize(new_header_image, 
                                                 width=750, 
                                                 height=300, 
                                                 crop_to_fit=True)

                header_image_large = images.resize(new_header_image, 
                                                   width=1000, 
                                                   height=400, 
                                                   crop_to_fit=True)

                post_photo_thumb = PostPhoto(image=header_image_thumb)
                post_photo_thumb.put()

                post_photo_small = PostPhoto(image=header_image_small)
                post_photo_small.put()

                post_photo_med = PostPhoto(image=header_image_med)
                post_photo_med.put()

                post_photo_large = PostPhoto(image=header_image_large)
                post_photo_large.put()

                post.header_image_thumb = str(post_photo_thumb.key().id())
                post.header_image_small = str(post_photo_small.key().id())
                post.header_image_med = str(post_photo_med.key().id())
                post.header_image_large = str(post_photo_large.key().id())

            if submit:
                post.put()
            self.render("editpost.html", post=post)




"""
Delete post handler
"""
class DeletePostHandler(Handler):
    def post(self):
        post_id = self.request.get("id")

        if post_id:
            post = Post.get_by_id(int(post_id))

            # only user who created post can delete it
            if post:
                if not(self.user and post.author_id == str(self.user.key().id())):
                    self.redirect('/signup')
                    return

                post.delete()
 
                # this feels hacky, but it prevents the post list from loading
                # before the post is deleted
                time.sleep(2)

        self.redirect("/postlist")



"""
Settings page, user can change some of their information from here
"""
class UserPage(UserSettingsHandler):
    def get(self):
        self.render("user.html")

'''
Logout page
'''
class LogoutPage(Handler):
    def get(self):
        self.logout()
        self.redirect("/")

"""
Login/New user signup page
"""
class SignupPage(UserSettingsHandler):
    def get(self):

        # this page is not accessible by a logged in user
        if self.is_logged_in():
            self.redirect("/")
            return

        self.render("signup.html")

    def post(self):

        # get submitted values
        if self.request.get("frm_submit") == "login":
            username = self.request.get("login_username")
            password = self.request.get("login_password")

            retry_params = {
                "login_username": username,
                "login_signup": False
            }

            if not (username and password):
                self.render("signup.html", **retry_params)
                return


            user = User.login(username, password)
            if not user:
                return

            self.login(str(user.key().id()))
            self.redirect("/")

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

            photo = PostPhoto.get_by_id(int(img_id))
            
            if photo and photo.image:
                self.response.headers["Content-Type"] = "image/jpeg"
                self.response.out.write(photo.image)

"""
Home page handler
"""
class MainPage(Handler):
    def get(self):
        posts = Post.all().order('-created')
        self.render("blog.html", posts=posts)

"""
Single post page handler
"""
class PostPage(Handler):
    def get(self, post_id):
        if post_id and post_id.isdigit():
            key = db.Key.from_path('Post', int(post_id))
            post = db.get(key)
            if post:
                self.render("post.html", post=post)
            else:
                self.redirect("/")

"""
Handler for new post submissions
"""
class NewPostPage(Handler):

    def get(self):
        if not self.is_logged_in():
            self.redirect("/signup")
            return

        self.render("newpost.html")


    def post(self):

        title = self.request.get("title")
        content = self.request.get("content")
        header_image_original = self.request.get("img")

        params = {
            "title": title,
            "content": content,
            "header_image_original": header_image_original
        }

        if not (title or content or header_image_original):
            self.render("newpost.html", **params)
            return

        """
        create different image sizes from original, put in datastore, 
        store id of each in post object
        """
        header_image_thumb = images.resize(header_image_original, 
                                           height=200)

        header_image_small = images.resize(header_image_original, 
                                           width=500, 
                                           height=200, 
                                           crop_to_fit=True)

        header_image_med = images.resize(header_image_original, 
                                         width=750, 
                                         height=300, 
                                         crop_to_fit=True)

        header_image_large = images.resize(header_image_original, 
                                           width=1000, 
                                           height=400, 
                                           crop_to_fit=True)

        post_photo_thumb = PostPhoto(image=header_image_thumb)
        post_photo_thumb.put()

        post_photo_small = PostPhoto(image=header_image_small)
        post_photo_small.put()

        post_photo_med = PostPhoto(image=header_image_med)
        post_photo_med.put()

        post_photo_large = PostPhoto(image=header_image_large)
        post_photo_large.put()

        # create post object
        post = Post(title=title, 
                    content=content, 
                    author_id=str(self.user.key().id()))

        post.header_image_thumb = str(post_photo_thumb.key().id())
        post.header_image_small = str(post_photo_small.key().id())
        post.header_image_med = str(post_photo_med.key().id())
        post.header_image_large = str(post_photo_large.key().id())

        post.put()

        


app = webapp2.WSGIApplication([('/', MainPage),
                               ('/newpost', NewPostPage),
                               ('/postimg', PostImageHandler),
                               ('/userimg', UserImageHandler),
                               ('/signup', SignupPage),
                               ('/user', UserPage),
                               ('/logout', LogoutPage),
                               ('/post/([0-9]+)', PostPage),
                               ('/postlist', UserPostsPage),
                               ('/delete', DeletePostHandler),
                               ('/edit/([0-9]+)', EditPostPage)])