from google.appengine.ext import db
from user import User

class Comment(db.Model):
	post_id = db.IntegerProperty(required=True)
	user_id = db.IntegerProperty(required=True)
	content = db.TextProperty(required=True)
	created = db.DateTimeProperty(auto_now_add=True)

	def get_user_name(self):
		if self.user_id:
			key = db.Key.from_path('User', int(self.user_id))
			user = db.get(key)

			if user:
				return user.get_full_name()

	def get_formatted_text(self):
		if self.content:
			return self.content.replace('\n', '<br>')