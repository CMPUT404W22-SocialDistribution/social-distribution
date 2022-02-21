from django.db import models
import uuid
from author_manager.models import Author

class Category(models.Model):
    text = models.CharField(max_length=30)

class Post(models.Model):
    type = models.CharField(max_length=50, default='post')
    title = models.CharField(max_length=200)
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    source = models.CharField(max_length=300, blank=True)
    origin = models.CharField(max_length=300, blank=True)
    description = models.CharField(max_length=300, blank=True, null=True)

    class ContentType(models.TextChoices):
        MARKDOWN = 'text/markdown',
        PLAIN = 'text/plain',
        APPLICATION = 'application/base64',
        PNG = 'image/png;base64',
        JPEG = 'image/jpeg;base64'
    
    content_type = models.CharField(
                    max_length=50,
                    choices=ContentType.choices,
                    default=ContentType.PLAIN
                )
    content = models.TextField()
    author = models.ForeignKey(
                Author,
                on_delete=models.CASCADE,
                null = True,
                related_name='posts'
            )
    categories = models.ManyToManyField( Category, blank=True)
    published = models.DateTimeField(auto_now_add=True)
    
    class VisibilityType(models.TextChoices):
        PUBLIC = 'public',
        PRIVATE = 'private',
        FRIENDS = 'friends'

    visibility = models.CharField(
                    max_length=30,
                    choices=VisibilityType.choices,
                    default=VisibilityType.PUBLIC
                )
    unlisted = models.BooleanField(default=False)
    


