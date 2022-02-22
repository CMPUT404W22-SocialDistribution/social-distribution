from django.db import models
from django.contrib.auth.models import User
import uuid

class Author(models.Model):
    def short_uuid():
        return uuid.uuid4().hex[:8]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='author')
    type = models.CharField(max_length=50, default="author")
    id = models.CharField(primary_key=True, default=short_uuid, max_length = 8, editable=False, unique=True)
    host = models.CharField(max_length=500, default='http://127.0.0.1:8000/', blank=True)
    displayName = models.CharField(max_length=200, default=f"{str(user)}")
    github = models.CharField(max_length=200, blank=True)
    profileImage = models.ImageField(upload_to='images/', blank=True, null=True)

    birthday = models.CharField(max_length=100, null=True, blank=True)
    email = models.EmailField(max_length=100, unique=True, blank=True, null=True, default=None)
    about = models.CharField(max_length=1000, blank=True, null=True)

    @property
    def url(self):
        return self.host + 'authors/' + str(self.id)
   

    def __str__(self):
        return self.displayName
