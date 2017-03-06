from google.appengine.ext import db

class Post(db.Model):
    title = db.StringProperty(required=True)
    content = db.TextProperty(required=True)
    header_image = db.StringProperty()
    header_image_small = db.StringProperty()
    header_image_large = db.StringProperty()
    created = db.DateTimeProperty(auto_now_add=True)
    author_id = db.StringProperty(required=True)

    def get_author_name(self):
    	author_key = db.Key.from_path('User', int(self.author_id))
    	author = db.get(author_key)
    	return author.first_name + " " + author.last_name
