from django.test import TestCase
from django.contrib.auth.models import User
from author_manager.models import Author
from posts.models import Post, Comment
from django.test import TestCase

class PostTest(TestCase):
    def setUp(self):
        user = User.objects.create_user(username='cmput404', password='cmput404')
        self.author = Author.objects.create(user=user)
        self.post = Post.objects.create(author=self.author)

    def test_type_set_on_creation(self):
        self.assertEqual(self.post.type, 'post')
    
    def test_description_set_on_creation(self):
        self.assertEqual(self.post.description, 'No description')
    
    def test_content_type_set_on_creation(self):
        self.assertEqual(self.post.content_type, 'text/plain')
    
    def test_visibility_set_on_creation(self):
        self.assertEqual(self.post.visibility, 'public')
    
class CommentTest(TestCase):
    def setUp(self):
        user = User.objects.create_user(username='cmput404', password='cmput404')
        self.author = Author.objects.create(user=user)
        self.post = Post.objects.create(author=self.author)
        self.comment = Comment.objects.create(author=self.author, post=self.post, comment="Hello")
    
    def test_type_set_on_creation(self):
        self.assertEqual(self.comment.type, 'comment')
    def test_content_type_set_on_creation(self):
        self.assertEqual(self.comment.contentType, 'text/plain')
    def test_comment_set_on_creation(self):
        self.assertEqual(self.comment.comment, 'Hello')