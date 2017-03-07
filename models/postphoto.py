from google.appengine.ext import db

class PostPhoto(db.Model):
    image = db.BlobProperty(required=True)