from django.test import TestCase
from django.contrib.auth.models import User
from author_manager.models import Author
from django.test import TestCase

class AuthorTest(TestCase):
    def setUp(self):
        user = User.objects.create_user(username='cmput404', password='cmput404')
        self.author = Author.objects.create(user=user)
        self.author.save()
    
    def test_host_set_on_creation(self):
        self.assertEquals(self.author.host, 'http://127.0.0.1:8000/')
    
    def test_url_set_on_creation(self):
        author_id = self.author.id
        url = 'http://127.0.0.1:8000/authors/'+str(author_id)
        self.assertEquals(self.author.url, url)

    def test_author_one_to_one_user(self):
        user = User.objects.get(username='cmput404')
        self.assertEquals(user, self.author.user)

