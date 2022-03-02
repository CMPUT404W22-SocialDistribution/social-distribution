import os
import tempfile
from base64 import b64encode
from collections import namedtuple

from django.conf import settings
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse
from rest_framework.test import APITestCase

from author_manager.models import Author
from posts.models import Post


class PostsTest(APITestCase):

    def setUp(self):
        self.username = 'test1'
        self.password = 'password1'
        user = User.objects.create_user(username=self.username, password=self.password, is_active=True)
        self.author = Author.objects.create(user=user)
        self.post = Post.objects.create(author=self.author, title='Test Post', content='Test post content',
                                        content_type='text/plain', visibility='public')
        self.post3 = Post.objects.create(author=self.author, title='Test Post 3', content='Test post 3 content',
                                         content_type='text/plain', visibility='public')

        # author2 with post2
        user2 = User.objects.create_user(username='test2', password='password2', is_active=True)
        self.author2 = Author.objects.create(user=user2)
        self.post2 = Post.objects.create(author=self.author2)

        # login user1 account
        self.client.login(username='test1', password='password1')
        self.url = reverse('posts:all_posts_api')

    def test_get_all_posts(self):
        credentials = b64encode(f'{self.username}:{self.password}'.encode('utf-8'))
        response = self.client.get(
            self.url,
            HTTP_AUTHORIZATION='Basic {}'.format(credentials.decode('utf-8')),
        )
        self.assertEqual(response.status_code, 200)


class MyPostsTest(APITestCase):

    def setUp(self):
        username = 'test2'
        password = 'password2'
        user = User.objects.create_user(username='test1', password='password1', is_active=True)
        self.author = Author.objects.create(user=user)
        self.post = Post.objects.create(author=self.author, title='Test Post', content='Test post content',
                                        content_type='text/plain', visibility='public')
        self.post3 = Post.objects.create(author=self.author, title='Test Post 3', content='Test post 3 content',
                                         content_type='text/plain', visibility='public')

        # author2 with post2
        user2 = User.objects.create_user(username='test2', password='password2', is_active=True)
        self.author2 = Author.objects.create(user=user2)
        self.post2 = Post.objects.create(author=self.author2)

        # login user1 account
        self.client.login(username='test2', password='password2')
        self.url = reverse('posts:my_posts_api', args=[self.author.id])
        self.credentials = b64encode(f'{username}:{password}'.encode('utf-8'))

    def test_get_my_posts(self):
        response = self.client.get(
            self.url,
            HTTP_AUTHORIZATION='Basic {}'.format(self.credentials.decode('utf-8')),
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['posts']), 2)

    def test_post_my_posts_unauthorized(self):
        request_body = {
            'title': 'Test Post',
            'content_type': 'text/plain',
            'content': 'Test post content',
            'visibility': 'public',
        }
        response = self.client.post(
            self.url,
            request_body,
            format='json'
        )
        self.assertEqual(response.status_code, 401)

    def test_post_my_posts_authorized(self):
        self.url = reverse('posts:my_posts_api', args=[self.author2.id])
        request_body = {
            'title': 'Test Post',
            'content_type': 'text/plain',
            'content': 'Test post content',
            'visibility': 'public',
            'commentsSrc': []
        }
        response = self.client.post(
            self.url,
            request_body,
            format='json'
        )
        self.assertEqual(response.status_code, 200)
        new_post = Post.objects.filter(author=self.author2).order_by('-published')[0]

        self.assertEqual(new_post.title, 'Test Post')
        self.assertEqual(new_post.author, self.author2)
        self.assertEqual(new_post.content, 'Test post content')


class PostDetailTest(APITestCase):

    def setUp(self):
        username = 'test1'
        password = 'password1'
        user = User.objects.create_user(username='test1', password='password1', is_active=True)
        self.author = Author.objects.create(user=user)
        self.post = Post.objects.create(author=self.author, title='Test Post', content='Test post content',
                                        content_type='text/plain', visibility='private')

        user2 = User.objects.create_user(username='test2', password='password2', is_active=True)
        self.author2 = Author.objects.create(user=user2)

        self.url = reverse('posts:post_detail_api', args=[self.author.id, self.post.id])
        self.credentials = b64encode(f'{username}:{password}'.encode('utf-8'))

    def test_get_post(self):
        self.client.login(username='test1', password='password1')
        response = self.client.get(
            self.url,
            HTTP_AUTHORIZATION='Basic {}'.format(self.credentials.decode('utf-8')),
        )
        self.assertEqual(response.status_code, 200)

    def test_get_post_unauthorized(self):
        username = 'test2'
        password = 'password2'
        self.credentials = b64encode(f'{username}:{password}'.encode('utf-8'))

        self.client.login(username='test2', password='password2')
        response = self.client.get(
            self.url,
            HTTP_AUTHORIZATION='Basic {}'.format(self.credentials.decode('utf-8')),
        )
        self.assertEqual(response.status_code, 404)

    def test_post_post(self):
        # edit post
        self.client.login(username='test1', password='password1')
        request_body = {
            'title': self.post.title,
            'content': 'Update post content',
            'content_type': self.post.content_type,
            'visibility': self.post.visibility
        }
        response = self.client.post(
            self.url,
            request_body,
            format='json'
        )
        self.assertEqual(response.status_code, 200)
        updated_post = Post.objects.get(id=self.post.id)
        self.assertEqual(updated_post.content, 'Update post content')

    def test_post_post_unauthorized(self):
        self.client.login(username='test2', password='password2')
        request_body = {
            'title': self.post.title,
            'content': 'Update post content',
            'content_type': self.post.content_type,
            'visibility': self.post.visibility
        }
        response = self.client.post(
            self.url,
            request_body,
            format='json'
        )
        self.assertEqual(response.status_code, 401)

    def test_delete_post(self):
        self.client.login(username='test1', password='password1')

        response = self.client.delete(
            self.url,
            HTTP_AUTHORIZATION='Basic {}'.format(self.credentials.decode('utf-8'))
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Post.objects.filter(id=self.post.id).count(), 0)

    def test_delete_post_unauthorized(self):
        username = 'test2'
        password = 'password2'
        self.credentials = b64encode(f'{username}:{password}'.encode('utf-8'))
        response = self.client.delete(
            self.url,
            HTTP_AUTHORIZATION='Basic {}'.format(self.credentials.decode('utf-8'))
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(Post.objects.filter(id=self.post.id).count(), 1)

    def test_put_post(self):
        self.client.login(username='test1', password='password1')
        self.url = reverse('posts:post_detail_api', args=[self.author.id, '086abc57'])
        request_body = {
            'title': 'New Title',
            'content': 'New content',
            'content_type': 'text/plain',
            'visibility': 'public',
            'commentsSrc': []
        }
        response = self.client.put(
            self.url,
            request_body,
            format='json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['title'], 'New Title')
        self.assertEqual(response.data['content'], 'New content')

    def test_put_post_unauthorized(self):
        self.client.login(username='test2', password='password2')
        self.url = reverse('posts:post_detail_api', args=[self.author.id, '086abc57'])
        request_body = {
            'title': 'New Title',
            'content': 'New content',
            'content_type': 'text/plain',
            'visibility': 'public'
        }
        response = self.client.put(
            self.url,
            request_body,
            format='json'
        )
        self.assertEqual(response.status_code, 401)

    def test_put_existing_post(self):
        self.client.login(username='test1', password='password1')
        request_body = {
            'title': 'New Title',
            'content': 'New content',
            'content_type': 'text/plain',
            'visibility': 'public'
        }
        response = self.client.put(
            self.url,
            request_body,
            format='json'
        )
        self.assertEqual(response.status_code, 400)


@override_settings(MEDIA_ROOT=settings.BASE_DIR / 'test_media')
class ImagePostTest(APITestCase):
    UserCredentials = namedtuple('UserCredentials', ['username', 'password'])

    def setUp(self):
        self.user1_credentials = self.UserCredentials('test1', 'password1')

        user1 = User.objects.create_user(username=self.user1_credentials.username,
                                         password=self.user1_credentials.password,
                                         is_active=True)
        self.author1 = Author.objects.create(user=user1)

        self.post_with_no_image = Post.objects.create(author=self.author1, title='Test Post with no image',
                                                      content='Test post content',
                                                      content_type='text/plain', visibility='private')

        temp_jpg = tempfile.NamedTemporaryFile(mode='rb', suffix=".jpg")
        self.post_with_image = Post.objects.create(author=self.author1, title='Test Post with image',
                                                   content='Test post content',
                                                   content_type='text/plain', visibility='private',
                                                   image=SimpleUploadedFile(name=temp_jpg.name,
                                                                            content=temp_jpg.read(),
                                                                            content_type='image/jpeg'))

    def tearDown(self):
        self.post_with_image.image.delete()
        os.rmdir(os.path.join(settings.MEDIA_ROOT, self.post_with_image.id))

    @classmethod
    def tearDownClass(cls):
        os.rmdir(settings.MEDIA_ROOT)

    def test_get_post_image_not_found_returns_404(self):
        self.client.login(username=self.user1_credentials.username, password=self.user1_credentials.password)
        self.url = reverse('posts:post_image', args=[self.author1.id, self.post_with_no_image.id])

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)

    def test_get_post_image_unauthorized_returns_401(self):
        self.url = reverse('posts:post_image', args=[self.author1.id, self.post_with_image.id])

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 401)

    def test_get_post_image_success_redirects_to_image_url(self):
        self.client.login(username=self.user1_credentials.username, password=self.user1_credentials.password)
        self.url = reverse('posts:post_image', args=[self.author1.id, self.post_with_image.id])

        response = self.client.get(self.url)
        self.assertRedirects(response, expected_url=self.post_with_image.image.url, fetch_redirect_response=False)
