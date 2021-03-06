from google.appengine.ext import db
from post import Post
from user import User


class Comment(db.Model):
    """ A comment submitted by a user about a Post entity

    Attributes:
        post: reference to post this comment is tied to
        user: reference to user who submitted this comment
        content: body of comment
        created: when comment was posted
    """
    post = db.ReferenceProperty(Post, collection_name="comments")
    user = db.ReferenceProperty(User, collection_name="comments")
    content = db.TextProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)


    def get_user_name(self):
        """ Gets first and last name of user tied to this comment

        Returns:
            first and last name of user as a string
        """
        return self.user.get_full_name()


    def get_formatted_text(self):
        """ Gets content formatted for html pages

        Returns:
            Formatted content
        """
        if self.content:
            return self.content.replace('\n', '<br>')


    def user_is_author(self, user_id):
        """ Returns if user_id is the same as the user who
        created this comment

        """
        return self.user.key().id() == user_id
