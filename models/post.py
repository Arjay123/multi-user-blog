from google.appengine.ext import db
from google.appengine.api import images

from postphoto import PostPhoto
from comment import Comment

class Post(db.Model):
    title = db.StringProperty(required=True)
    content = db.TextProperty(required=True)
    header_image_thumb = db.StringProperty()
    header_image_small = db.StringProperty()
    header_image_med = db.StringProperty()
    header_image_large = db.StringProperty()
    snippet = db.TextProperty()
    created = db.DateTimeProperty(auto_now_add=True)
    author_id = db.StringProperty(required=True)
    views = db.IntegerProperty(default=0)
    likes = db.ListProperty(int, default=[])


    def get_comments(self):
        q = Comment.gql("WHERE post_id=%s ORDER BY created DESC" % str(self.key().id()))
        return q.run()

    def add_comment(self, user_id, content):
        comment = Comment(user_id=user_id, post_id=self.key().id(), content=content)
        comment.put()


    def delete_comment(self, comment_id):
        comment = self.get_comment(comment_id)

        if comment:
            self.comments.remove(comment.key().id())
            comment.delete()

    def get_comment(self, comment_id):
        key = db.Key.from_path('Comment', int(comment_id))
        comment = db.get(key)

        return comment

    def like(self, author_id):
        if not self.user_liked(author_id):
            self.likes.append(author_id)


    def unlike(self, author_id):
        if self.user_liked(author_id):
            self.likes.remove(author_id)

    def user_liked(self, author_id):
        return author_id in self.likes

    def inc_views(self):
        self.views = self.views + 1


    """
    create different image sizes from original, put in datastore, 
    store id of each in post object
    """
    def change_header_image(self, new_header_image):
        # delete current images from datastore
        for photo_id in [self.header_image_thumb, 
                      self.header_image_small,
                      self.header_image_med,
                      self.header_image_large]:
            if photo_id:
                PostPhoto.delete_by_id(photo_id)

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

        self.header_image_thumb = str(post_photo_thumb.key().id())
        self.header_image_small = str(post_photo_small.key().id())
        self.header_image_med = str(post_photo_med.key().id())
        self.header_image_large = str(post_photo_large.key().id())

    def get_formatted_text(self):
        if self.content:
            return self.content.replace('\n', '<br>')


    def create_snippet(self):
        if self.content:
            self.snippet = self.content.split('\n')[0]


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
            PostPhoto.delete_by_id(photo_id)

        super(Post, self).delete()
