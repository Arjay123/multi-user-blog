import os
import jinja2
import webapp2

from google.appengine.ext import ndb
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

class Post(ndb.Model):
	title = ndb.StringProperty(required=True)
	content = ndb.TextProperty(required=True)
	header_image = ndb.BlobProperty()
	created = ndb.DateTimeProperty(auto_now_add=True)


class MainPage(Handler):
    def get(self):
    	self.render("blog.html")

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
							   ('/newpost', NewPostPage),])