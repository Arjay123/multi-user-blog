import os
import jinja2
import webapp2

from google.appengine.ext import db
from google.appengine.api import images


template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), 
                               autoescape=True)


class Handler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))



class Post(db.Model):
	title = db.StringProperty(required=True)
	content = db.TextProperty(required=True)
	header_image = db.BlobProperty()
	created = db.DateTimeProperty(auto_now_add=True)


class ImageHandler(Handler):
	def get(self):
		img_id = self.request.get("img_id")
		if img_id and img_id.isdigit():

			post = Post.get_by_id(int(img_id))
			

			if post and post.header_image:
				self.response.headers["Content-Type"] = "image/jpeg"
				self.response.out.write(post.header_image)
			else:
				print "poopoo"

		else:
			print "poop"



class MainPage(Handler):
    def get(self):
    	posts_cursor = Post.gql("ORDER BY created DESC")
    	posts = posts_cursor.fetch(limit=10)
    	self.render("blog.html", posts=posts)

class NewPostPage(Handler):
	def get(self):
		self.render("newpost.html")

	def post(self):
		title = self.request.get("title")
		content = self.request.get("content")

		header_image = self.request.get("img")
		header_image = images.resize(header_image, 500, 200)

		valid = True

		post = Post(title=title, content=content)
		post.header_image = header_image
		post.put()



app = webapp2.WSGIApplication([('/', MainPage),
							   ('/newpost', NewPostPage),
							   ('/img', ImageHandler)])