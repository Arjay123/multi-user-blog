from comment import Comment
from google.appengine.ext import db
from google.appengine.api import images
from postphoto import PostPhoto
from user import User


class Post(db.Model):
    """ A blog post submitted by a user
    
    Attributes:
        title: title of the post
        content: body of the post
        header_image_thumb: id of the thumbnail of header image
        header_image_small: id of the small size header image
        header_image_med: id of the med size header image
        header_image_large: id of the large size header image
        snippet: the first paragraph of the body
        created: when the post was submitted
        author_id: id of the user who submitted the post
        views: number of views this post has gotten
        likes: ids of users who liked the post
        comment_num: number of comments on this post
    """
    title = db.StringProperty(required=True)
    content = db.TextProperty(required=True)
    header_image_thumb = db.StringProperty()
    header_image_small = db.StringProperty()
    header_image_med = db.StringProperty()
    header_image_large = db.StringProperty()
    snippet = db.TextProperty()
    created = db.DateTimeProperty(auto_now_add=True)
    author_id = db.IntegerProperty(required=True)
    views = db.IntegerProperty(default=0)
    likes = db.ListProperty(int, default=[])
    comment_num = db.IntegerProperty(default=0)


    @classmethod
    def create_post(cls, title, content, author_id, img):
        """ Create post
        
        Creates post object w/ snippet and header images

        Args:
            title - title of post
            content - post body
            author_id - id of author
            img - img to be resized for header images
        """
        post = Post(title=title, 
                    content=content, 
                    author_id=author_id)

        post.change_header_image(img)
        post.create_snippet()

        post.put()


    def get_comments(self):
        """ Gets all comments associated with this post

        Returns:
            Returns iterable to loop through results of query
        """
        q = Comment.gql("WHERE post_id=%s ORDER BY created DESC" 
            % str(self.key().id()))

        return q.run()


    def add_comment(self, user_id, content):
        """ Creates new comment and increments comment count
        
        Comment created is associated with a single user and a single post

        Args:
            user_id - id of user who submitted
            content - body of comment
        """
        comment = Comment(user_id=user_id,
                          post_id=self.key().id(),
                          content=content)
        comment.put()

        self.comment_num = self.comment_num + 1
        self.put()


    def delete_comment(self, comment_id):
        """ Deletes comment using id and decrements comment count
        
        Args:
            comment_id - id of comment
        """
        comment = Comment.get_by_id(comment_id)
        if comment:
            comment.delete()

            self.comment_num = self.comment_num - 1
            self.put()


    def user_can_like(self, author_id):
        """ Returns if user is allowed to like the post 

        """
        return author_id != self.author_id


    def like(self, author_id):
        """ Adds a user to list of users who like this post
        
        User is not added if they are already in the list or the author

        Args: 
            author_id - user_id
        """
        if self.user_can_like(author_id) and not self.user_liked(author_id):
            self.likes.append(author_id)


    def unlike(self, author_id):
        """ Removes user from list of users who like this post
        
        Args: 
            author_id - Id of user
        """
        if self.user_liked(author_id):
            self.likes.remove(author_id)


    def user_liked(self, author_id):
        """ Returns whether user is in ist of users who like this post
        
        Args:
            author_id - Id of user

        Return:
            Boolean value
        """
        return author_id in self.likes


    def inc_views(self):
        """ Increment view count by 1

        """
        self.views = self.views + 1


    def change_header_image(self, new_header_image):
        """ Changes header image of this post

        Creates different sizes of original image and stores each
        size as a PostPhoto object, stores id of each photo in 
        this post's attributes

        Args:
            new_header_image - original image file

        """

        # delete current images from datastore
        for photo_id in [self.header_image_thumb, 
                      self.header_image_small,
                      self.header_image_med,
                      self.header_image_large]:
            if photo_id:
                PostPhoto.delete_by_id(photo_id)

        # insert new images of varying sizes to datastore
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

        # store ids as attributes
        self.header_image_thumb = str(post_photo_thumb.key().id())
        self.header_image_small = str(post_photo_small.key().id())
        self.header_image_med = str(post_photo_med.key().id())
        self.header_image_large = str(post_photo_large.key().id())


    def get_formatted_text(self):
        """ Gets content formatted for html pages

        Returns:
            Formatted content
        """
        if self.content:
            return self.content.replace('\n', '<br>')


    def create_snippet(self):
        """ Creates a snippet of the full post body

        Snippet created by using the first paragraph    
        """
        if self.content:
            self.snippet = self.content.split('\n')[0]


    def get_author_name(self):
        """ Gets full name of author of the post
        
        Returns:
            Returns first and last name of the author
        """
        author = User.get_by_id(self.author_id)
        if author:
            return author.get_full_name()

    
    def delete(self):
        """ Overrides db.Model delete, entity deletes all associated 
        content before deleting itself

        """
        for photo_id in [self.header_image_thumb, 
                      self.header_image_small,
                      self.header_image_med,
                      self.header_image_large]:
            PostPhoto.delete_by_id(photo_id)

        for comment in self.get_comments():
            comment.delete()

        super(Post, self).delete()
