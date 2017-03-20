import hashlib
import hmac
import os
import time
import random
import re
import jinja2
import webapp2
import decorators
from string import letters
from urllib import urlopen
from PIL import Image

from google.appengine.api import images
from google.appengine.ext import db
from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers

from models.user import User
from models.post import Post
from models.postphoto import PostPhoto




template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), 
                               autoescape=True)

secret = "TMnhG42cnYMCjWcB"
USER_COOKIE_KEY = "user"


def render_str(template, **params):
    """ Use jinja to convert templates to string to render html
    
    Args:
        params - unpacked dictionary of parameters to be used in template

    Returns:
        Rendered template as string w/ params included

    This code was taken from Udacity's Full Stack Engineering course
    """
    t = jinja_env.get_template(template)
    return t.render(params)

"""
Base class for page handlers, contains common methods
needed by any handler
"""
class Handler(webapp2.RequestHandler):

    def write(self, *a, **kw):
        """ Writes template to response
            
            This code was taken from Udacity's Full Stack Engineering course
        """
        self.response.out.write(*a, **kw)

    
    def render_str(self, template, **params):
        """ 
        before rendering the template, gets stored user object
        and passes to page params
        
        This code was taken from Udacity's Full Stack Engineering course
        """
        params['user'] = self.user
        return render_str(template, **params)


    def render(self, template, **kw):
        """ Calls render str to convert template to string format and
        writes to response
        
        This code was taken from Udacity's Full Stack Engineering course
        """
        self.write(self.render_str(template, **kw))


    def make_secure_val(self, val):
        """
        create cookie value by hashing value w/ secret key

        Args:
            val - value to secure

        Returns:
            str containing value and hashed value separated by |

        This code was taken from Udacity's Full Stack Engineering course
        """
        return '%s|%s' % (val, hmac.new(secret, val).hexdigest())


    def check_secure_val(self, secure_val):
        """
        check cookie value w/ hash value to ensure it hasn't been modified by
        the requesting user

        return: cookie value if valid, else None

        This code was taken from Udacity's Full Stack Engineering course
        """
        val = secure_val.split('|')[0]
        if secure_val == self.make_secure_val(val):
            return val

    
    def set_cookie(self, name, value):
        """  sets cookie value
        
        This code was taken from Udacity's Full Stack Engineering course
        """
        h = self.make_secure_val(value)
        self.response.headers.add_header('Set-Cookie', 
                '%s=%s; Path=/' % (name, str(h)))

    
    def get_cookie(self, name):
        """ Returns cookie value if valid
        
        This code was taken from Udacity's Full Stack Engineering course
        """
        cookie_val = self.request.cookies.get(name)
        return cookie_val and self.check_secure_val(cookie_val)


    def initialize(self, *a, **kw):
        """
        called before loading page, if user is logged in, gets user from db
        using the id stored in USER_COOKIE_KEY cookie

        This code was taken from Udacity's Full Stack Engineering course
        """
        webapp2.RequestHandler.initialize(self, *a, **kw)
        uid = self.get_cookie(USER_COOKIE_KEY)
        self.user = uid and User.get_by_id(int(uid))


    def login(self, uid):
        """ logs in user by setting hashed cookie value to user ID in client
            
        """
        self.set_cookie(USER_COOKIE_KEY, uid)


    def logout(self):
        """ delete user cookie value from client

        """
        self.set_cookie(USER_COOKIE_KEY, "")
        self.user = None


    def is_logged_in(self):
        """ Check if user is logged in

        """
        return self.user


class UserSettingsHandler(Handler):
    """
    Handler base class for any pages that edit the User object in the db

    Attributes:
        USER_RE - valid user regex
        PASS_RE - valid password regex
        EMAIL_RE - valid email regex
    """

    USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
    def valid_username(self, username):
        return username and self.USER_RE.match(username)

    PASS_RE = re.compile(r"^.{3,20}$")
    def valid_password(self, password):
        return password and self.PASS_RE.match(password)

    EMAIL_RE  = re.compile(r'^[\S]+@[\S]+\.[\S]+$')
    def valid_email(self, email):
        return not email or self.EMAIL_RE.match(email)


class UserPostsPage(Handler):
    """ List of posts created by current logged in user
    
    """
    def get(self):
        posts = Post.gql("WHERE author_id=%s ORDER BY created DESC" % 
            str(self.user.key().id()))
        self.render("post_list.html", posts=posts.fetch(limit=None))


class EditPostPage(Handler):
    """ Edit existing post page

    """
    @decorators.post_exists
    @decorators.user_logged_in
    @decorators.user_owns_post
    def get(self, post):
        self.render("editpost.html", post=post)

    @decorators.post_exists
    @decorators.user_logged_in
    @decorators.user_owns_post
    def post(self, post):
        new_title = self.request.get("title")
        new_content = self.request.get("content")
        new_header_image = self.request.get("img")

        post.edit_post(new_title, new_content, new_header_image)

        self.render("editpost.html", post=post)


class DeletePostHandler(Handler):
    """
    Delete post handler
    """
    @decorators.post_exists
    @decorators.user_logged_in
    @decorators.user_owns_post
    def get(self, post):
        post.delete()

        # this feels hacky, but it prevents the page from loading
        # before the post is deleted
        time.sleep(2)

        self.redirect("/postlist")


class UserPage(UserSettingsHandler):
    """
    Settings page, user can change some of their information from here
    """
    @decorators.user_logged_in
    def get(self):
        self.render("user.html")

    @decorators.user_logged_in
    def post(self):
        first_name = self.request.get("first_name")
        last_name = self.request.get("last_name")
        password = self.request.get("password")
        confirm_pw = self.request.get("confirm_pw")
        email = self.request.get("email")
        img = self.request.get("img")
        bio = self.request.get("bio")

        valid = True
        pw_error = ""
        confirm_pw_error = ""

        if password:
            if password != confirm_pw:
                valid = False
                confirm_pw_error = "Passwords do not match"
            elif not self.valid_password(password):
                valid = False
                pw_error = "Invalid password"
            else:
                self.user.change_password(password)

        if valid:
            settings = {
                "first_name": first_name,
                "last_name": last_name,
                "password": password,
                "email": email,
                "img": img,
                "bio": bio
            }

            self.user.change_user_settings(**settings)

        self.render("user.html", 
                    pw_error=pw_error, 
                    confirm_pw_error=confirm_pw_error)


class LogoutPage(Handler):
    """ Logout page

    """
    @decorators.user_logged_in
    def get(self):
        if self.is_logged_in():
            self.logout()
        self.redirect("/")


class SignupPage(UserSettingsHandler):
    """ Login/New user signup page

    """
    @decorators.user_logged_out
    def get(self):
        if self.is_logged_in():
            self.redirect("/")
            return

        self.render("signup.html")

    @decorators.user_logged_out
    def post(self):

        # login
        if self.request.get("frm_submit") == "login":
            username = self.request.get("login_username")
            password = self.request.get("login_password")

            retry_params = {
                "login_username": username,
            }

            if not (username and password):
                self.render("signup.html", **retry_params)
                return


            user = User.login(username, password)
            if not user:
                return

            self.login(str(user.key().id()))
            self.redirect("/")

        # signup
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
                return


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
                user.change_user_settings(img=avatar_image)


            self.login(str(user.key().id()))
            self.redirect("/user")


class UserImageHandler(Handler):
    """ Handler for rendering user avatar images stored as BlobProperty values

    """
    @decorators.user_exists
    @decorators.user_img_exists
    def get(self, img):
        self.response.headers["Content-Type"] = "image/jpeg"
        self.response.out.write(img)



class PostImageHandler(Handler):
    """ Handler for rendering post header images stored as BlobProperty values
    
    """
    @decorators.post_img_exists
    def get(self, photo):
        self.response.headers["Content-Type"] = "image/jpeg"
        self.response.out.write(photo.image)


class MainPage(Handler):
    """ Home page handler

    """
    def get(self):
        posts = Post.all().order('-created').run(limit=9)
        self.render("blog.html", posts=posts)



class PostPage(Handler):
    """ Single post page

    """
    @decorators.post_exists
    def get(self, post):
        # if post_id and post_id.isdigit():
        #     post = Post.get_by_id(int(post_id))
        post.inc_views()
        post.put()
        params = { "post": post }
        if self.user:
            params["user_liked"] = post.user_liked(self.user.key().id())
        self.render("post.html", **params)


    @decorators.post_exists
    def post(self, post):

        submit = self.request.get("submit")
        if submit:
            if submit == "like":
                post.like(self.user.key().id())
                post.put()
            elif submit == "unlike":
                post.unlike(self.user.key().id())
                post.put()
            elif submit == "comment":
                comment = self.request.get("comment")
                if comment:
                    post.add_comment(self.user.key().id(), comment)
                    time.sleep(2)
            elif submit == "uncomment":
                comment_id = self.request.get("comment_id")
                if comment_id:
                    comment_id = int(comment_id)
                    post.delete_comment(comment_id)
                    time.sleep(2)


        
        self.redirect("/post/%s" % str(post_id))


class DeleteCommentHandler(Handler):
    """ Handler for deleting comments

    """
    @decorators.comment_exists
    @decorators.post_exists
    @decorators.user_logged_in
    @decorators.user_owns_comment
    def post(self, post, comment):
        post.delete_comment(comment.key().id())
        time.sleep(2)

        self.redirect("/post/%s" % str(post.key().id()))


class AuthorsPage(Handler):
    """ Authors page 

    """
    def get(self):
        authors = User.gql("ORDER BY first_name, last_name")
        self.render("authors.html", authors=authors)


class AuthorPage(Handler):
    """ Single Author Page

    """
    @decorators.user_exists
    def get(self, user):
        posts = Post.gql("WHERE author_id=%s ORDER BY created DESC" % str(user.key().id()))
        self.render("author.html", author=user, posts=posts)


class AboutPage(Handler):
    """ About page

    """
    def get(self):
        self.render("about.html")


class NewPostPage(Handler):
    """ Handler for new post submissions

    """
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

        # create post
        post = Post.create_post(title, 
                         content, 
                         self.user.key().id(), 
                         header_image_original)

        self.redirect("/post/%s" % str(post.key().id()))


        
class InitHandler(Handler):
    """ This is for testing only, initializes db with sample users and posts
        Remove when in production
    """
    def get(self):

        for user in User.all():
            user.delete()

        for post in Post.all():
            post.delete()

        users_dicts = [
            {
               "username": "cwuser", 
               "pw": "cw", 
               "fname": "Clarence", 
               "lname": "Wendle", 
               "email": "ClarenceW@email.com", 

               "bio": "Clarence is the main character of Clarence. "
               "Clarence's distinct perspective can transform any "
               "circumstance, however mundane, into the best day ever! "
               "His beliefs, outlook and experiences are all uniquely his "
               "own. Clarence leads with his heart, reacting to life "
               "with unfailing excitement and enthusiasm. He values his "
               "friends more than gold. In Pretty Great Day with a "
               "Girl, he is shown to be friends with everybody in Aberdale "
               "except Victor. Clarence loves everything because to "
               "Clarence, everything is amazing. He is most definitely "
               "the emotional third of this trio of friends. Despite "
               "all this, he's not very bright. It has been shown "
               "multiple times that his optimism also transforms "
               "him to a dimwit. In Average Jeff, it shown that he scored "
               "no only high crayon, he's the lowest, implying "
               "that his stupidity lead him up to this, however due to "
               "his habits and his describe stupidity.",

               "url": "https://pbs.twimg.com/profile_images/554702195220697089/kb5fWogP.jpeg"
            },
            {
               "username": "rsuser", 
               "pw": "rs", 
               "fname": "Ryan", 
               "lname": "Sumouski", 
               "email": "RyanS@email.com", 

               "bio": "Ryan 'Sumo' Sumouski is one of the three main "
               "protagonists (More as a deuteragonist) in Clarence. He "
               "is one of Clarence's friends. He loves to do all sorts "
               "of crazy things so that he can enjoy having fun with "
               "Clarence, Jeff, and everyone else. Like his friends, he "
               "is socially awkward. He was originally voiced by Jason "
               "Marsden in the 'Pilot,' but was replaced by Tom Kenny "
               "in the series.",

               "url": "http://vignette4.wikia.nocookie.net/clarence/images/d/d8/Bird_Boy_Man_57.png/revision/latest?cb=20160120051349"
            },
            {
               "username": "jruser", 
               "pw": "jr", 
               "fname": "Jeff", 
               "lname": "Randell", 
               "email": "JeffR@email.com", 

               "bio": "Jeff Randell is one of the three main characters "
               "in Clarence. Clarence's best friend, Jeff, is a bit of "
               "a square with a long list of phobias, but even someone "
               "as uptight as Jeff can't help but have fun when Clarence "
               "is around. He is both the tritagonist and a semi-antagonist.",

               "url": "http://vignette2.wikia.nocookie.net/clarence/images/6/6c/This_is_Jeffrey_Randell_from_the_6_clock_news.png/revision/latest?cb=20150407232224"
            },
            {
               "username": "cbuser", 
               "pw": "cb", 
               "fname": "Courage", 
               "lname": "Bagge", 
               "email": "CourageB@email.com", 

               "bio": "Despite his signature cowardly demeanor, Courage "
               "does live up to the meaning of his name. Because of a "
               "kidnapping incident with his parents, he was abandoned as "
               "a puppy, found by Muriel, and began fearing everything. "
               "This fear is easily swallowed, however, when Muriel's "
               "safety is put into jeopardy or trouble falls upon him "
               "in general. Not only because he wishes to protect "
               "Muriel, but because the events of his most painful memory "
               "drives him to do so in fear of losing another loved one.",

               "url": "http://vignette1.wikia.nocookie.net/courage/images/1/11/Courage.a.jpg/revision/latest/scale-to-width-down/310?cb=20110304185658"
            },
            {
               "username": "asuser", 
               "pw": "as", 
               "fname": "Arnold", 
               "lname": "Shortman", 
               "email": "ArnoldS@email.com", 

               "bio": "Arnold Phillip Shortman is a fictional character "
               "created by Craig Bartlett. He has featured in claymation "
               "shorts and comics, but his main role has been the main "
               "protagonist of the Nickelodeon animated television series "
               "Hey Arnold!. His head is shaped like a giant football, "
               "thus earning him the nickname \"Football Head\".",

               "url": "http://vignette3.wikia.nocookie.net/heyarnold/images/f/f6/Arnold.jpg/revision/latest/scale-to-width-down/200?cb=20140706192844"
            }

        ]

        lorem_ipsums = [
            "Lorem ipsum dolor sit amet, pri vocent partiendo ne, in eam "
            "quis quidam ceteros, ea vim amet modo reformidans. Ludus "
            "posidonium an mea, scripta omnesque expetendis usu in, "
            "quis tation labore ne usu. Dicta essent sit et. Sea ex dicant "
            "propriae conceptam. Invenire scribentur ne pri, id elitr "
            "recteque torquatos his. Eu officiis luptatum pro.\n",

            "Ex labores dissentias eum. Has liber vituperatoribus ea. "
            "Elit feugiat ut sed, ius mundi invidunt aliquando et. Eu "
            "democritum interesset ullamcorper nec, ei nam prodesset "
            "delicatissimi. Everti molestiae no duo, duo nusquam "
            "fierent ei, nonumes eligendi ex mei.\n",

            "Est ad saperet definiebas scriptorem. Ex vel melius probatus "
            "ullamcorper, mel congue petentium an. Sit epicuri evertitur "
            "id, usu ea fugit altera. Cu usu option instructior. An mea "
            "vitae feugiat consequuntur, ea has dicta facilisi iudicabit. "
            "Nullam timeam an sed, no eum paulo omnesque tacimates.\n",

            "Ius cu error nominavi, duo elit saepe causae ne. At tractatos "
            "explicari vis, esse fugit tritani pro ne. An vim rebum dictas "
            "nostrum. Est quot nominati an. Dico solum vix ei.\n",

            "Magna virtute vix ea, rationibus constituto et eos. Decore "
            "tamquam delenit sea ei, appetere pertinax pro et. Ut qui "
            "pertinax expetenda, ad eam etiam dignissim. Ne mel malorum "
            "expetenda. Stet eirmod ad his, mei doctus pertinax ea.\n",

            "Prompta saperet pertinacia sit no. Ei per vivendo partiendo. "
            "Ius solet delenit volutpat ex, cu augue ponderum quo. Vim zril "
            "mentitum appetere id, id ridens petentium vituperata vis.\n",

            "Ferri principes sit ut. Ad soleat voluptua pro. Pri pericula "
            "explicari te, albucius percipit te vim. Cum tempor oblique "
            "atomorum ex, sanctus volumus mediocrem ne sed. Ad veritus "
            "consequat vel, vis cu graeco singulis facilisis.\n",

            "Illud patrioque evertitur sit in. Ex reque sensibus efficiantur "
            "vel. Sed cu quis affert, vero prima iracundia vis cu. Mea "
            "etiam luptatum et, pri meis quando iracundia at. Meis "
            "everti ei usu, eu his choro dolorum.\n",

            "Cu quo soluta partiendo, petentium assueverit constituam has "
            "in. Animal qualisque an eos, odio unum detracto ei vel. At "
            "his dicta utamur. No putant laboramus his, ei cum tollit "
            "delectus lucilius, et duo quaeque accusamus. Est eu consul "
            "insolens atomorum. Mel illud nusquam suscipiantur ei, per id "
            "quot adipisci. Sea te veritus vocibus incorrupte.\n",

            "Usu in quot repudiare interesset, novum epicurei "
            "vituperatoribus et cum. Ea mei movet nullam neglegentur, "
            "fabulas saperet te eos. Qui stet oporteat indoctum no, "
            "unum nostrum deleniti ne sit. Ferri pertinax eam no, ex "
            "latine persecuti per. Ut quo luptatum gloriatur democritum.\n"
        ]

        imgs = [
            "https://images3.alphacoders.com/675/675273.jpg",
            "https://blogs-images.forbes.com/erikkain/files/2017/01/Switch-gamepad.jpg",
            "http://sawadacoffee.com/wp-content/uploads/Sawada-Coffee-10DEC2015-003.jpg",
            "https://www.nobrowcoffee.com/wp-content/uploads/2016/04/coffee-wallpaper-1306-1433-hd-wallpapers.jpg",
            "https://cdn0.vox-cdn.com/uploads/chorus_image/image/48851021/shutterstock_249549703.0.0.jpg",
            "http://media3.s-nbcnews.com/j/newscms/2016_32/1665641/ss-160812-twip-02_3380f5e9d30b766138155f8c3f11f9a8.nbcnews-fp-1200-800.jpg"
        ]

        titles = [
            "Lifehax: Turn your pizza upside down for more flavor",
            "Chemistry 101: Sandals are OK",
            "I will beat you at FIFA no questions asked",
            "One easy trick to win at Smash4: Play Bayo or Cloud",
            "Zelda BOTW is my spirit animal",
            "10 reasons why Arjay is cool",
            "I love Frank Ocean",
            "11 things you didn't know about clickbait titles"
        ]

        user_ids = {}
        user_comments = {
            "asuser": 
                [
                   "What's wrong with old things? Some old things are great.",
                   "Hey, leave those kids alone.",
                   "Hey Grandpa, I've got a problem. " 
                ],
            "cwuser": 
                [
                    "I think that frog's dead",
                    "Mmmm...flavory",
                    "Hit the pinata"
                ],
            "cbuser": 
                [
                    "AAAAAAAAAAAAAAAAAAAA!", 
                    "Muriel, I'll save you!",
                    "The things I do for love."
                ],
            "jruser": 
                [
                    "You can't make me, I'm not moving an inch.",
                    "Why don't we just ask someone?",
                    "I was worried you guys got lost or something."
                ],
            "rsuser": 
                [
                    "What are you talkin' about? Pinatas are awesome.",
                    "Hit the pinata"
                ]
        }

        # create users
        for user_dict in users_dicts:
            user = User.register(user_dict["username"], 
                                 user_dict["fname"], 
                                 user_dict["lname"], 
                                 user_dict["pw"], 
                                 user_dict["email"])

            response = urlopen(user_dict["url"])
            img = response.read()
            avatar_image = images.resize(img, 150, 150, crop_to_fit=True)
            user.avatar_image = avatar_image
            user.bio = user_dict["bio"]
            user.put()

            user_ids[user.username] = user.key().id()

        # create posts
        for _ in range(random.randint(15, 25)):
            title = random.choice(titles)
            content = '\n'.join([random.choice(lorem_ipsums) 
                                 for x in range(random.randint(3, 10))])

            response = urlopen(random.choice(imgs))
            header_img = response.read()
            author_id = user_ids[random.choice(user_ids.keys())]

            # create post object
            post = Post(title=title, 
                        content=content, 
                        author_id=int(author_id),
                        views=random.choice(range(25, 100)))
            try:
                post.change_header_image(header_img)
            except images.BadImageError:
                print img_url

            post.create_snippet()
            post.put()

            # likes and comments
            users_who_like = random.sample(user_ids.keys(), 
                                           random.randint(0, 5))

            for key in users_who_like:
                post.like(user_ids[key])
                post.add_comment(int(user_ids[key]), 
                                     random.choice(user_comments[key]))

            post.put()


# routing
app = webapp2.WSGIApplication([('/', MainPage),
                               ('/newpost', NewPostPage),
                               ('/postimg/([0-9]+)', PostImageHandler),
                               ('/userimg/([0-9]+)', UserImageHandler),
                               ('/signup', SignupPage),
                               ('/user', UserPage),
                               ('/logout', LogoutPage),
                               ('/post/([0-9]+)', PostPage),
                               ('/postlist', UserPostsPage),
                               ('/delete/([0-9]+)', DeletePostHandler),
                               ('/edit/([0-9]+)', EditPostPage),
                               ('/authors', AuthorsPage),
                               ('/author/([0-9]+)', AuthorPage),
                               ('/init', InitHandler),
                               ('/about', AboutPage),
                               ('/uncomment', DeleteCommentHandler)])