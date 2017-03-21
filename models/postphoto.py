from google.appengine.api import images
from google.appengine.ext import db
from post import Post

THUMB_HEIGHT = 200
SMALL_HEIGHT = 200
SMALL_WIDTH = 500
MED_HEIGHT = 300
MED_WIDTH = 750
LARGE_HEIGHT = 400
LARGE_WIDTH = 1000


class PostPhoto(db.Model):

    """ A photo object tied to a single post
    
    Attributes:
        image - blob property of the image
    """
    THUMB = "thumb"
    SMALL = "small"
    MED = "med"
    LARGE = "large"


    image = db.BlobProperty(required=True)
    post = db.ReferenceProperty(Post, collection_name="photos")
    size = db.StringProperty(choices=(THUMB, SMALL, MED, LARGE), 
                             required=True)


    

    @classmethod
    def delete_by_id(cls, photo_id):
        """ Deletes PostPhoto entity using id

        """
        photo = PostPhoto.get_by_id(int(photo_id))
        if photo:
            photo.delete()


    @classmethod
    def add_image_to_post(cls, post, new_header_image):
        # insert new images of varying sizes to datastore
        header_image_thumb = images.resize(new_header_image, 
                                   height=THUMB_HEIGHT)

        header_image_small = images.resize(new_header_image, 
                                           width=SMALL_WIDTH, 
                                           height=SMALL_HEIGHT, 
                                           crop_to_fit=True)

        header_image_med = images.resize(new_header_image, 
                                         width=MED_WIDTH, 
                                         height=MED_HEIGHT, 
                                         crop_to_fit=True)

        header_image_large = images.resize(new_header_image, 
                                           width=LARGE_WIDTH, 
                                           height=LARGE_HEIGHT, 
                                           crop_to_fit=True)

        post_photo_thumb = PostPhoto(image=header_image_thumb,
                                     post=post,
                                     size=PostPhoto.THUMB)
        post_photo_thumb.put()

        post_photo_small = PostPhoto(image=header_image_small,
                                     post=post,
                                     size=PostPhoto.SMALL)
        post_photo_small.put()

        post_photo_med = PostPhoto(image=header_image_med,
                                     post=post,
                                     size=PostPhoto.MED)
        post_photo_med.put()

        post_photo_large = PostPhoto(image=header_image_large,
                                     post=post,
                                     size=PostPhoto.LARGE)
        post_photo_large.put()
