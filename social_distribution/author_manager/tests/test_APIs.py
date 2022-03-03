
from collections import namedtuple

from django.conf import settings
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse
from rest_framework.test import APITestCase

from author_manager.models import Author
from base64 import b64encode



class AuthorsTest(APITestCase):

    def setUp(self):
        self.username = 'test'
        self.password = 'password'
        user = User.objects.create_user(username=self.username, password=self.password, is_active=True)
        self.author = Author.objects.create(user=user)

        # login user account
        self.client.login(username='test', password='password')
        self.url = reverse('author_manager:getAllAuthors')
        self.credentials = b64encode(f'{self.username}:{self.password}'.encode('utf-8'))
    def test_get_all_authors(self):
        response = self.client.get(
            self.url, 
            HTTP_AUTHORIZATION='Basic {}'.format(self.credentials.decode('utf-8')),
        )       
        self.assertEqual(response.status_code, 200)

class AuthorProfileTest(APITestCase):
    def setUp(self):
        self.username = 'test'
        self.password = 'password'
        user = User.objects.create_user(username=self.username, password=self.password, is_active=True)
        self.author = Author.objects.create(user=user)

        #Create anothe author profile
        user1 = User.objects.create_user(username="test1", password="password1", is_active=True)
        self.author1 = Author.objects.create(user=user1)

        # login user account
        self.client.login(username='test', password='password')
        self.url = reverse('author_manager:profile', args=[self.author.id])  #Checkout other author profile
        self.credentials = b64encode(f'{self.username}:{self.password}'.encode('utf-8'))

    def test_get_own_author_profile(self):
        response = self.client.get(
            self.url, 
            HTTP_AUTHORIZATION='Basic {}'.format(self.credentials.decode('utf-8')),
        )
        self.assertEqual(response.status_code, 200)
    def test_get_other_author_profile(self):
        self.url = reverse('author_manager:profile', args=[self.author1.id])  
        response = self.client.get(
            self.url, 
            HTTP_AUTHORIZATION='Basic {}'.format(self.credentials.decode('utf-8')),
        )
        self.assertEqual(response.status_code, 200)

    def test_post_profile_authorized(self):
        self.url = reverse('author_manager:profile', args=[self.author.id]) 
        request_body = {'id': self.author.id, 'name': 'John Doe'}
        response = self.client.post(
                    self.url,
                    request_body,
                    format='json'
        )
        self.assertEqual(response.status_code, 200)

    def test_post_profile_unauthorized(self):
        self.url = reverse('author_manager:author', args=[self.author1.id])
        request_body = {'id': self.author1.id, 'name': 'JohDoe'} # user tries to edit user1 profile
        response = self.client.post(
                    self.url,
                    request_body,
                    format='json'
        )
        self.assertEqual(response.status_code, 401)
       