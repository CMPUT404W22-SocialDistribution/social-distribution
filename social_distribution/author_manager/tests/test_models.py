from django.test import TestCase
from django.contrib.auth.models import User
from author_manager.models import Author, FriendRequest
from django.test import TestCase

class AuthorTest(TestCase):
    def setUp(self):
        user = User.objects.create_user(username='cmput404', password='cmput404')
        self.author = Author.objects.create(user=user)
        self.author.save()
    
    def test_host_set_on_creation(self):
        self.assertEquals(self.author.host, 'http://127.0.0.1:8000/')
    
    def test_author_one_to_one_user(self):
        user = User.objects.get(username='cmput404')
        self.assertEquals(user, self.author.user)

class FriendRequestTest(TestCase):
    def setUp(self):
        user1 = User.objects.create_user(username='user1', password='testuser')
        user2 = User.objects.create_user(username='user2', password='testuser')
        self.author1 = Author.objects.create(user=user1)
        self.author2 = Author.objects.create(user=user2)
        self.author1.save()
        self.author2.save()

        self.friendrequest = FriendRequest.objects.create(actor=self.author1, object=self.author2)
        self.friendrequest.save()
    
    def test_exist_friendrequest(self):
        exist_frequest = FriendRequest.objects.get(actor=self.author1, object=self.author2)
        self.assertEqual(self.friendrequest, exist_frequest)

    def test_not_exist_friendrequest(self):
        not_exist_frequest = FriendRequest.objects.filter(actor=self.author2, object=self.author1)
        self.assertEqual(len(not_exist_frequest), 0)

    def test_correct_actor_object(self):
        self.assertEqual(self.friendrequest.actor.id, self.author1.id)
        self.assertEqual(self.friendrequest.object.id, self.author2.id)