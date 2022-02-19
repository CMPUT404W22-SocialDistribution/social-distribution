from django.db import models
from django.contrib.auth.models import User
import uuid

class Author(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='author')
    type = models.CharField(max_length=50, default="Author")
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    host = models.CharField(max_length=500, default='http://localhost:8000/', blank=True)
    displayName = models.CharField(max_length=200, default=f"{str(user)}")
    github = models.CharField(max_length=200, blank=True)
    profileImage = models.ImageField(upload_to='images/', blank=True, null=True)

    @property
    def url(self):
        return self.host + 'authors/' + str(self.id)

    def __str__(self):
        return self.displayName

        