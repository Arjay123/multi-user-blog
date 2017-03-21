
from google.appengine.ext import db
from google.appengine.api import images
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
        author: reference to user who submitted the post
        views: number of views this post has gotten
        likes: ids of users who liked the post
        comment_num: number of comments on this post
    """
    title = db.StringProperty(required=True)
    content = db.TextProperty(required=True)
    snippet = db.TextProperty()
    created = db.DateTimeProperty(auto_now_add=True)
    author = db.ReferenceProperty(User, collection_name="posts")
    views = db.IntegerProperty(default=0)
    likes = db.ListProperty(int, default=[])


    @classmethod
    def create_post(cls, title, content, author):
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
                    author=author)

        post.create_snippet()

        post.put()
        return post


    def edit_post(self, new_title, new_content):
        """ Edit post
        
        Post only pushes to datastore if any attributes have changed

        Args:
            new_title - new title 
            new_content - new body
            new_image - new header image
        """
        submit = False

        if new_title:
            submit=True
            self.title = new_title

        if new_content:
            submit=True
            self.content = new_content

        if submit:
            self.put()


    def get_comments(self):
        """ Gets all comments associated with this post

        Returns:
            Returns iterable to loop through results of query
        """
        return self.comments


    def get_comments_num(self):
        """ Returns number of comments on this post
            
            Returns:
                Integer representing number of comments 
        """
        return self.comments.count()


    def user_is_author(self, author_id):
        """ Returns if user is the author of the post 

        """
        return author_id == self.author.key().id()


    def like(self, author_id):
        """ Adds a user to list of users who like this post
        
        User is not added if they are already in the list or the author

        Args: 
            author_id - user_id
        """
        if not self.user_is_author(author_id) and not self.user_liked(author_id):
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
        return self.author.get_full_name()


    def get_header_image_id(self, size):
        """ Gets image id of certain size
        
        Args:
            size - size of image to retrieve

        Returns:
            Integer representing id of image retrieved
            None if not found
        """
        print size
        res = self.photos.filter("size =", size).get()

        if res:
            return res.key().id()


    def delete_header_images(self):
        """ Deletes all associated images

        """
        for photo in self.photos:
            photo.delete()


    def delete(self):
        """ Overrides db.Model delete, entity deletes all associated 
        content before deleting itself

        """
        self.delete_header_images()

        for comment in self.get_comments():
            comment.delete()

        super(Post, self).delete()
