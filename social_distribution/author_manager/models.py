from django.db import models
from django.contrib.auth.models import User
import uuid

class Author(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='author')
    type = models.CharField(max_length=50, default="author")
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    host = models.CharField(max_length=500, default='http://127.0.0.1:8000/', blank=True)
    displayName = models.CharField(max_length=200, default=f"{str(user)}")
    github = models.CharField(max_length=200, blank=True, unique=True)
    profileImage = models.ImageField(upload_to='images/', blank=True, null=True)

    @property
    def url(self):
        return self.host + 'authors/' + str(self.uuid)
    @property
    def id(self):
        return self.host + 'authors/' + str(self.uuid)

    def __str__(self):
        return self.displayName