from functools import wraps

from google.appengine.ext import db
from models.post import Post
from models.user import User


def post_exists(function):
    """ Check if post exists
    
    If post exists, returns post and post_id to function that called
    this decorator function.

    Else, calls 404 error

    Args:
        post_id - id of post to retrieve

    Pass:
        post_id - id of post found
        post - post found
    """
    @wraps(function)
    def wrapper(self, post_id, **kwargs):
        key = db.Key.from_path("Post", int(post_id))
        post = db.get(key)
        if post:
            kwargs['post'] = post
            return function(self, **kwargs)
        else:
            print "post doesnt exist"
            self.error(404)
            return
    return wrapper


def user_logged_in(function):
    """ Check if user is logged in before continuing
    
    This decorator is used in combination with other decorators to check
    if a user is logged in before performing actions that affect the
    datastore such as editing and deleting posts or comments

    If user logged in, continue
    Else, 404 error

    """
    @wraps(function)
    def wrapper(self, **kwargs):
        if self.user:
            return function(self, **kwargs)
        else:
            print "not logged in"
            self.redirect("/signup")
            return
    return wrapper


def user_logged_out(function):
    """ Check if no user is logged in before continuing

    """
    @wraps(function)
    def wrapper(self):
        if not self.user:
            return function(self)
        else:
            self.redirect("/")
            return
    return wrapper


def user_owns_post(function):
    """ Check if user created post

    If user created post, continue
    Else, 404 error
    
    This decorator should be used after user_logged_in to ensure
    user exists before attempting to access user attributes
    """
    @wraps(function)
    def wrapper(self, post):
        if post.user_is_author(self.user.key().id()):
            return function(self, post=post)
        else:
            print "aint yo post"
            self.error(404)
            return
    return wrapper


def user_exists(function):
    """ Check if user exists
    
    If user exists, return user and id,
    else, 404 error

    Args:
        user_id - id of user to retrieve
    """
    @wraps(function)
    def wrapper(self, user_id):
        key = db.Key.from_path("User", int(user_id))
        user = db.get(key)
        if user:
            return function(self, user_id, user)
        else:
            print "that aint nobody"
            self.error(404)
            return
    return wrapper


def user_owns_comment(function):
    """ Check if user owns comment

    """
    @wraps(function)
    def wrapper(self, comment, **kwargs):
        if comment.user_is_author(self.user.key().id()):
            return function(self, comment=comment, **kwargs)
        else:
            print "that aint your comment"
            self.error(404)
            return
    return wrapper


def comment_exists(function):
    """ Check if comment exists

    If comment exists, return comment and id
    else, 404 error

    Args:
        commend_id - id of comment to retrieve
    """
    @wraps(function)
    def wrapper(self, *args):
        comment_id = self.request.get("comment_id")
        if not comment_id:
            print "no comment sent"
            self.error(404)
            return

        key = db.Key.from_path("Comment", int(comment_id))
        comment = db.get(key)

        if comment:
            return function(self, post_id=comment.post_id, comment=comment)
        else:
            print "comment dont exist"
            self.error(404)
            return
    return wrapper





            