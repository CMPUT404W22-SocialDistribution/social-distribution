from django.test import TestCase
from django.contrib.auth.models import User
from author_manager.models import Author, Inbox, FriendRequest
from django.test import TestCase, Client
from django.urls import reverse
from django.shortcuts import redirect

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
        # create inbox object when signup
        inbox = Inbox(author=self.author)
        inbox.save()
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

    def test_profile_get(self):
        url = reverse('author_manager:profile', args=[self.author.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'author_profile/profile.html')

    def test_profile_edit_authorized(self):
        url = reverse('author_manager:editProfile', args=[self.author.id])
        request = {
            'displayName': 'NEW JOHN DOE',
            'github': 'johndoe'
        }
        response = self.client.post(
            url,
            request
        )
        redirect_url = reverse('author_manager:profile', args=[self.author.id])
        self.assertRedirects(response, redirect_url, status_code=302, target_status_code=200, fetch_redirect_response=True)

    def test_friends_get(self):
        url = reverse('author_manager:friends', args=[self.author.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'friends/friends.html')

    def test_inbox_get(self):
        url = reverse('author_manager:inbox', args=[self.author.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'inbox/inbox.html')

# class FriendRequestSend(TestCase):
#     def setUp(self):
#         self.client = Client()
#         user = User.objects.create_user(username='test1', password='password1', is_active=True)
#         self.author = Author.objects.create(user=user)
#         self.client.login(username="test1", password="password1")

#         # create another author to send friend request to
#         user1 = User.objects.create_user(username='test2', password='password2', is_active=True)
#         self.author1 = Author.objects.create(user=user1)
#         Inbox.objects.create(author=self.author1)

#         self.url = str(self.author.host) + "search/authors?q=test2"
    
#     def test_send_friend_request(self):
#         requestbody={'object_id': self.author1.id}
#         response = self.client.post(self.url, requestbody)
#         self.assertEqual(response.status_code, 302)

#         friendrequest = FriendRequest.objects.get(actor=self.author)
#         self.assertEqual(friendrequest.actor.id, self.author.id)
#         self.assertEqual(friendrequest.object.id, self.author1.id)

# class FriendRequestAccept(TestCase):
#     def setUp(self):
#         self.client = Client()
#         user = User.objects.create_user(username='test1', password='password1', is_active=True)
#         self.author = Author.objects.create(user=user)
#         Inbox.objects.create(author=self.author)
#         self.client.login(username="test1", password="password1")

#         # create another author to accept friend request
#         user1 = User.objects.create_user(username='test2', password='password2', is_active=True)
#         self.author1 = Author.objects.create(user=user1)

#         # create a friend request to accept
#         self.friendrequest = FriendRequest.objects.create(actor=self.author1, object=self.author)

#         self.url = reverse('author_manager:inbox', args=[self.author.id])
    
#     def test_accept_friend_request(self):
#         requestbody={'type': 'befriend', 'actor_id': self.author1.id}
#         response = self.client.post(self.url, requestbody)
#         self.assertEqual(response.status_code, 302)

#         self.assertTrue(self.author1 in self.author.followers.all())

class FriendUnfriend(TestCase):
    def setUp(self):
        self.client = Client()
        user = User.objects.create_user(username='test1', password='password1', is_active=True)
        self.author = Author.objects.create(user=user)
        self.client.login(username="test1", password="password1")

        # create another author to unfriend
        user1 = User.objects.create_user(username='test2', password='password2', is_active=True)
        self.author1 = Author.objects.create(user=user1)
        self.author.followings.add(self.author1)

        self.url = reverse('author_manager:friends', args=[self.author.id])
    
    def test_unfriend(self):
        requestbody={'object_id': self.author1.id}
        response = self.client.post(self.url, requestbody)
        self.assertEqual(response.status_code, 302)

        self.assertTrue(self.author1 not in self.author.followings.all())