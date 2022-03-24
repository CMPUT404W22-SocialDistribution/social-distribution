from django.shortcuts import redirect
from django.test import TestCase
from django.contrib.auth.models import User
from posts.models import Post, Comment
from author_manager.models import Author
from django.test import TestCase, Client
from django.urls import reverse 

class PostCreateTest(TestCase):
    def setUp(self):
        self.client = Client()
        user = User.objects.create_user(username='test1', password='password1', is_active=True)
        self.author = Author.objects.create(user=user)
        self.client.login(username='test1', password='password1')
        self.url = reverse('posts:post_create', args=[self.author.id])
        
    def test_create_post_form_get(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response,'posts/post_create.html')
    
    def test_create_post_post(self):

        request_body = {
                        'title':'Test Post',
                        'content_type':'text/plain',
                        'content':'Test post content',
                        'visibility':'public'
                        }
        response = self.client.post(self.url, request_body)
        self.assertEqual(response.status_code, 302)
        
        new_post = Post.objects.all().order_by('-published')[0]
        
        self.assertEqual(new_post.title, 'Test Post')
        self.assertEqual(new_post.content, 'Test post content')

class PostEditTest(TestCase):

    def setUp(self):

        self.client = Client()
        user = User.objects.create_user(username='test1', password='password1', is_active=True)
        self.author = Author.objects.create(user=user)
        self.post = Post.objects.create(author=self.author, title='Test Post', content='Test post content', content_type='text/plain', visibility='public')
        
        # author2 with post2
        user2 = User.objects.create_user(username='test2', password='password2', is_active=True)
        self.author2 = Author.objects.create(user=user2)
        self.post2 = Post.objects.create(author=self.author2)
        # login user1 account
        self.client.login(username='test1', password='password1')
        self.url = reverse('posts:post_edit', args=[self.author.id, self.post.id])
    
    def test_edit_post_form_get(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'posts/post_create.html')

    def test_edit_post_unauthorized_post(self):
        # user1 attempts to edit post2 of user2

        self.url = self.url = reverse('posts:post_edit', args=[self.author2.id, self.post2.id])
        request_body = {
                        'title': 'New title',
                        'content': 'Update post content',
                        'content_type': 'text/plain',
                        'visibility': 'public'
                        }
        response = self.client.post(self.url, request_body)
        self.assertEqual(response.status_code, 401)

    def test_edit_post_authorized_post(self):
        request_body = {
                        'title': self.post.title,
                        'content': 'Update post content',
                        'content_type': self.post.content_type,
                        'visibility': self.post.visibility
                        }
        response = self.client.post(self.url, request_body)
        redirect_url = reverse('posts:post_detail', args=[self.author.id, self.post.id])
        self.assertRedirects(response, redirect_url, status_code=302, target_status_code=200)

class PostDeleteTest(TestCase):

    def setUp(self):

        self.client = Client()
        user = User.objects.create_user(username='test1', password='password1', is_active=True)
        self.author = Author.objects.create(user=user)
        self.post = Post.objects.create(author=self.author, title='Test Post', content='Test post content', content_type='text/plain', visibility='public')
        
        # author2 with post2
        user2 = User.objects.create_user(username='test2', password='password2', is_active=True)
        self.author2 = Author.objects.create(user=user2)
        self.post2 = Post.objects.create(author=self.author2)
        # login user1 account
        self.client.login(username='test1', password='password1')
        self.url = reverse('posts:post_delete', args=[self.author.id, self.post.id])

    def test_delete_post_unauthorized_get(self):
        # user1 attempts to delete post2 of user2

        self.url = reverse('posts:post_delete', args=[self.author2.id, self.post2.id])
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 401)

    def test_delete_post_not_exist_get(self):
        # user1 attempts to edit non-existing post

        self.url = reverse('posts:post_delete', args=[self.author2.id, '086abc57'])
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)

    def test_delete_post_authorized_get(self):

        response = self.client.get(self.url)
        redirect_url = reverse('author_manager:home')
        self.assertRedirects(response, redirect_url, status_code=302, target_status_code=200)

class PostViewTest(TestCase):
    def setUp(self):

        self.client = Client()
        user = User.objects.create_user(username='test1', password='password1', is_active=True)
        self.author = Author.objects.create(user=user)
        self.post = Post.objects.create(author=self.author, title='Test Post', content='Test post content', content_type='text/plain', visibility='public')
        
        # author2 with post2
        user2 = User.objects.create_user(username='test2', password='password2', is_active=True)
        self.author2 = Author.objects.create(user=user2)
        self.post2 = Post.objects.create(author=self.author2, visibility='private')
        # login user1 account
        self.client.login(username='test1', password='password1')
        self.url = reverse('posts:post_detail', args=[self.author.id, self.post.id])

    def test_view_post_get(self):
        
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
    
    def test_view_private_post_get(self):

        self.url = reverse('posts:post_detail', args=[self.author2.id, self.post2.id])  
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)

    def test_view_post_not_exist_get(self):

        self.url = reverse('posts:post_detail', args=[self.author.id, '086abc57'])  
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)

class PostsListTest(TestCase):

    def setUp(self):

        self.client = Client()
        user = User.objects.create_user(username='test1', password='password1', is_active=True)
        self.author = Author.objects.create(user=user)
        # create posts for author 1
        self.post = Post.objects.create(author=self.author, title='Test Post', content='Test post content', content_type='text/plain', visibility='public')
        self.post2 = Post.objects.create(author=self.author, title='Test Post 2', content='Test post 2 content', content_type='text/plain', visibility='public')
        self.post3 = Post.objects.create(author=self.author, title='Test Post 3', content='Test post 3 content', content_type='text/plain', visibility='public')
        # create user for author 2
        user2 = User.objects.create_user(username='test2', password='password2', is_active=True)
        self.author2 = Author.objects.create(user=user2)

    def test_view_all_posts_unauthorized_get(self):
        # author2 attempts to see all posts of author1

        self.client.login(username='test2', password='password2')
        url = reverse('posts:posts', args=[self.author.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)
    
    def test_view_all_posts_authorized_get(self):

        self.client.login(username='test1', password='password1')
        url = reverse('posts:posts', args=[self.author.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

class CommentCreate(TestCase):
    def setUp(self):
        self.client = Client()
        user = User.objects.create_user(username='test1', password='password1', is_active=True)
        self.author = Author.objects.create(user=user)
        self.post = Post.objects.create(author=self.author, title='Test Post', content='Test post content', content_type='text/plain', visibility='public')
        
        self.client.login(username='test1', password='password1')
        self.url = reverse('posts:comments', args=[self.author.id, self.post.id])  

    def test_create_comment(self):

        request_body = {'comment': 'This is my first comment in this post', 'post': self.post.id}
        response = self.client.post(self.url, request_body)
        self.assertEqual(response.status_code, 200)
        
        new_comment = Comment.objects.all().order_by('-published')[0]
        self.assertEqual(new_comment.comment, 'This is my first comment in this post')

