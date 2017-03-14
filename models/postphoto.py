from google.appengine.ext import db


class PostPhoto(db.Model):
	""" A photo object tied to a single post
	
    Attributes:
		image - blob property of the image
    """
    image = db.BlobProperty(required=True)


    @classmethod
    def delete_by_id(cls, photo_id):
    	""" Deletes PostPhoto entity using id

    	"""
    	photo = PostPhoto.get_by_id(int(photo_id))
        if photo:
            photo.delete()