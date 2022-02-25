from django.conf.global_settings import MEDIA_ROOT
from django.db import models
import uuid
from author_manager.models import Author


class Category(models.Model):
    text = models.CharField(max_length=30)


class Post(models.Model):
    def short_uuid():
        return uuid.uuid4().hex[:8]

    def image_upload_path(instance, filename):
        """Upload an image to MEDIA_ROOT/<post ID>/<filename>"""
        return '{0}/{1}'.format(instance.id, filename)

    type = models.CharField(max_length=50, default='post')
    title = models.CharField(max_length=200)
    id = models.CharField(primary_key=True, default=short_uuid, max_length=8, editable=False, unique=True)
    source = models.CharField(max_length=300, blank=True)
    origin = models.CharField(max_length=300, blank=True)
    description = models.CharField(max_length=300, blank=True, null=True, default="No description")

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
    content = models.TextField(blank=True, default="")
    image = models.ImageField(upload_to=image_upload_path, null=True, blank=True)
    author = models.ForeignKey(
        Author,
        on_delete=models.CASCADE,
        null=True,
        related_name='posts'
    )
    categories = models.ManyToManyField(Category, blank=True)
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
    


class Comment(models.Model):
    def short_uuid():
        return uuid.uuid4().hex[:8]

    class ContentType(models.TextChoices):
        MARKDOWN = 'text/markdown',
        PLAIN = 'text/plain'



    type = models.CharField(max_length=50, default='comment')
    author = models.ForeignKey(
                Author,
                on_delete=models.CASCADE,
                null = True,
                related_name='post_comments'
            )
    comment = models.CharField(max_length=300, null=True)

    contentType = models.CharField(
                max_length=50,
                choices=ContentType.choices,
                default=ContentType.PLAIN)

    published = models.DateTimeField(auto_now_add=True)
    id = models.CharField(primary_key=True, default=short_uuid, max_length = 8, editable=False, unique=True)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name = "comments")
    
    
