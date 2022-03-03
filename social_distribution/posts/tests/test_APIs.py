from typing import OrderedDict
from django.urls import reverse
from rest_framework.test import APITestCase
from django.contrib.auth.models import User
from author_manager.models import Author
from posts.models import Post, Comment
from base64 import b64encode
import json

class PostsTest(APITestCase):

    def setUp(self):
        self.username = 'test1'
        self.password = 'password1'
        user = User.objects.create_user(username=self.username, password=self.password, is_active=True)
        self.author = Author.objects.create(user=user)
        self.post = Post.objects.create(author=self.author, title='Test Post', content='Test post content', content_type='text/plain', visibility='public')
        self.post3 = Post.objects.create(author=self.author, title='Test Post 3', content='Test post 3 content', content_type='text/plain', visibility='public')

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
        self.post = Post.objects.create(author=self.author, title='Test Post', content='Test post content', content_type='text/plain', visibility='public')
        self.post3 = Post.objects.create(author=self.author, title='Test Post 3', content='Test post 3 content', content_type='text/plain', visibility='public')

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
                        'title':'Test Post',
                        'content_type':'text/plain',
                        'content':'Test post content',
                        'visibility':'public',
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
                        'title':'Test Post',
                        'content_type':'text/plain',
                        'content':'Test post content',
                        'visibility':'public',
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
        self.post = Post.objects.create(author=self.author, title='Test Post', content='Test post content', content_type='text/plain', visibility='private')

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



class CommentsTest(APITestCase):

    def setUp(self):
        self.username = 'test'
        self.password = 'password'
        user = User.objects.create_user(username=self.username, password=self.password, is_active=True)
        self.author = Author.objects.create(user=user)
        self.post = Post.objects.create(author=self.author, title='POST TEST', 
                    content='THIS IS A POST TEST CONTENT', content_type='text/plain', visibility='public')
        self.comment1 = Comment.objects.create(author=self.author, comment='This is comment test 1',
                    contentType= 'text/plain', post=self.post )
       

       # Create another author
        user1 = User.objects.create_user(username='test1', password='password1', is_active=True)
        self.author1 = Author.objects.create(user=user1)  # Create new author comment on the same post
        self.comment2 = Comment.objects.create(author=self.author1, comment='This is comment test 2 by a different author',
                    contentType= 'text/plain', post=self.post )
        self.comment3 = Comment.objects.create(author=self.author1, comment='This is comment test 2',
                    contentType= 'text/plain', post=self.post )
        
        # login user account
        self.client.login(username='test', password='password')
        self.url = reverse('posts:comments_api', args=[self.author.id, self.post.id])
        self.credentials = b64encode(f'{self.username}:{self.password}'.encode('utf-8'))
    def test_get_all_comments(self):
        
        response = self.client.get(
                        self.url, 
                        HTTP_AUTHORIZATION='Basic {}'.format(self.credentials.decode('utf-8')),
                        )       
        self.assertEqual(response.status_code, 200)

    def test_post_comments(self): 
        request_body = {'comment': 'This is my first comment',}
        response = self.client.post(
                    self.url,
                    request_body,
                    format='json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['comment'], 'This is my first comment')
    