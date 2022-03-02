from django.test import TestCase
from django.contrib.auth.models import User
from author_manager.models import Author
from django.test import TestCase, Client
from django.urls import reverse 

class AuthenticationTest(TestCase):
    def setUp(self):
        self.client = Client()
        user = User.objects.create_user(username='test1', password='password1')
        Author.objects.create(user=user)
        user.is_active = True
        user.save()
        self.login_url= 'author_manager:login'
        self.signup_url= 'author_manager:sign_up'
        self.logout_url= 'author_manager:logout'
    
    def test_login_form(self):
        response = self.client.get(reverse(self.login_url))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/login.html')
    
    def test_login_valid(self):
        request = {
            'username': 'test1',
            'password': 'password1'
        }
        response = self.client.post(
            reverse(self.login_url),
            request
        )
        redirect_url = reverse('author_manager:home')
        self.assertRedirects(response, redirect_url, status_code=302, target_status_code=200, fetch_redirect_response=True)
        
    def test_sign_up_form(self):
        response = self.client.get(reverse(self.signup_url))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/signup.html')

    def test_signup_valid(self):
        request = {
            'username': 'test2',
            'password1': 'cmput404',
            'password2': 'cmput404'
        }
        response = self.client.post(
            reverse(self.signup_url),
            request
        )
        self.assertRedirects(response, reverse(self.login_url), status_code=302, target_status_code=200, fetch_redirect_response=True)

    def test_logout(self):
        response = self.client.get(reverse(self.logout_url))
        self.assertRedirects(response, '/login/?next=/logout/', status_code=302, target_status_code=200, fetch_redirect_response=True)
          
class ViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        user = User.objects.create_user(username='test1', password='password1')
        self.author = Author.objects.create(user=user, github='abramhindle')
        user.is_active = True
        user.save()
        self.client.login(username="test1", password="password1")

    def test_home_get(self):
        url = reverse('author_manager:home')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'author_manager/index.html')

    def test_github_events_get(self):
        url = reverse('author_manager:github')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)