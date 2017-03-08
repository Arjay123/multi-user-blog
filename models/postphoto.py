from google.appengine.ext import db

class PostPhoto(db.Model):
    image = db.BlobProperty(required=True)


    @classmethod
    def delete_by_id(cls, photo_id):
    	photo = PostPhoto.get_by_id(int(photo_id))
        if photo:
            photo.delete()