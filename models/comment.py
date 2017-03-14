from google.appengine.ext import db
from user import User


class Comment(db.Model):
    """ A comment submitted by a user about a Post entity

    Attributes:
        post_id: id of the post this comment is tied to
        user_id: id of the user who submitted this comment
        content: body of comment
        created: when comment was posted
    """
    post_id = db.IntegerProperty(required=True)
    user_id = db.IntegerProperty(required=True)
    content = db.TextProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)

    def get_user_name(self):
        """ Gets first and last name of user tied to this comment

        Returns:
            first and last name of user as a string
        """
        if self.user_id:
            key = db.Key.from_path('User', self.user_id)
            user = db.get(key)

            if user:
                return user.get_full_name()


    def get_formatted_text(self):
        """ Gets content formatted for html pages

        Returns:
            Formatted content
        """
        if self.content:
            return self.content.replace('\n', '<br>')



