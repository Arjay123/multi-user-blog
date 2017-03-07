from google.appengine.ext import db
from postphoto import PostPhoto

class Post(db.Model):
    title = db.StringProperty(required=True)
    content = db.TextProperty(required=True)
    header_image_thumb = db.StringProperty()
    header_image_small = db.StringProperty()
    header_image_med = db.StringProperty()
    header_image_large = db.StringProperty()
    created = db.DateTimeProperty(auto_now_add=True)
    author_id = db.StringProperty(required=True)



    def get_author_name(self):
        author_key = db.Key.from_path('User', int(self.author_id))
        author = db.get(author_key)
        return author.first_name + " " + author.last_name

    """
    Overrides db.Model delete, entity deletes all associated content before
    deleting itself
    """
    def delete(self):
        for photo_id in [self.header_image_thumb, 
                      self.header_image_small,
                      self.header_image_med,
                      self.header_image_large]:
            photo = PostPhoto.get_by_id(int(photo_id))
            if photo:
                photo.delete()

        super(Post, self).delete()
