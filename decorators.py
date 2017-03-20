

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

    def wrapper(self, post_id):
        key = db.Key.from_path("Post", int(post_id))
        post = db.get(key)
        if post:
            return function(self, post_id, post)
        else:
            self.error(404)
            return
    return wrapper


def user_owns_post(function):
    def wrapper(self, post_id, post):
        if post.user_is_author(self.user.key().id()):
            return function(self, post_id, post)
        else:
            self.error(404)
            return
    return wrapper


            