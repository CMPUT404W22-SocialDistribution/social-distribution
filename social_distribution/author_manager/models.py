import random
import uuid

from django.contrib.auth.models import User
from django.db import models
from django.core.validators import int_list_validator

class Author(models.Model):
    def randomImage():
        # randomize profile images 
        return str(random.randint(0, 6)) + '.svg'

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='author')
    type = models.CharField(max_length=50, default="author")
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True)
    host = models.CharField(max_length=200, default='http://127.0.0.1:8000/', blank=True)
    url = models.CharField(max_length=500, blank=True, null=True)
    displayName = models.CharField(max_length=200, default=f"{str(user)}")
    github = models.CharField(max_length=200, blank=True)
    profileImage = models.CharField(max_length=10, default=randomImage)

    # extra information
    birthday = models.CharField(max_length=100, null=True, blank=True)
    email = models.EmailField(max_length=100, unique=True, blank=True, null=True, default=None)
    about = models.CharField(max_length=1000, blank=True, null=True)

    # list of all followers and following authors. Used to get friends
    followings = models.ManyToManyField('self', symmetrical=False, blank=True, related_name='my_followings')
    followers = models.ManyToManyField('self', symmetrical=False, blank=True, related_name='my_followers')

    remote_followings = models.TextField(validators=[int_list_validator], null=True, blank=True)
    remote_followers = models.TextField(validators=[int_list_validator], null=True, blank=True)
    
    # list of remote friends' id
    def __str__(self):
        return self.displayName


class FriendRequest(models.Model):
    type = models.CharField(max_length=50, default='follow', editable=False)
    # sender
    actor = models.ForeignKey(Author, on_delete=models.CASCADE, related_name="actor")  # request
    # receiver
    object = models.ForeignKey(Author, on_delete=models.CASCADE, related_name="object")  # requested


class Inbox(models.Model):
    type = models.CharField(max_length=30, default='inbox', editable=False)
    author = models.OneToOneField(Author, on_delete=models.CASCADE, primary_key=True)
    # follows = models.ManyToManyField(FriendRequest, blank=True)
    # send posts to inbox
    posts = models.ManyToManyField('posts.Post', blank=True)
    # Send comment to inbox
    comments = models.ManyToManyField('posts.Comment', blank=True)
    likes = models.ManyToManyField('posts.Like', blank=True)

    follows = models.JSONField(default=list, blank=True)
    

    item = models.JSONField(default=dict)

