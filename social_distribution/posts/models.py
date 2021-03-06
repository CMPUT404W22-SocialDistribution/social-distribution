import uuid

from django.db import models

from author_manager.models import Author


# categories of post
class Category(models.Model):
    text = models.CharField(max_length=30)


class Post(models.Model):
    def image_upload_path(instance, filename):
        """Upload an image to MEDIA_ROOT/<post ID>/<filename>"""
        return '{0}/{1}'.format(instance.id, filename)

    type = models.CharField(max_length=50, default='post')
    title = models.CharField(max_length=200)
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True)
    # where the post was shared from 
    source = models.CharField(max_length=300, blank=True)
    # where the post was originated 
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
    # timestamp
    published = models.DateTimeField(auto_now_add=True)

    class VisibilityType(models.TextChoices):
        PUBLIC = 'public',
        PRIVATE = 'private',
        FRIENDS = 'friends'

    # post has 4 different types of visibility: public, friends, private, and private to specified friend 
    visibility = models.CharField(
        max_length=30,
        choices=VisibilityType.choices,
        default=VisibilityType.PUBLIC
    )

    visibleTo = models.CharField(max_length=200, blank=True)
    # if post is unlisted, it can only be seen with URI
    # image posts are set to unlisted automatically 
    # owner can see the post in My Posts page
    unlisted = models.BooleanField(default=False)
    remote = models.BooleanField(default=False)

    remote_author = models.JSONField(default=dict, null=True, blank=True)


class Comment(models.Model):
    class ContentType(models.TextChoices):
        MARKDOWN = 'text/markdown',
        PLAIN = 'text/plain'

    type = models.CharField(max_length=50, default='comment')
    author = models.ForeignKey(
        Author,
        on_delete=models.CASCADE,
        null=True,
        related_name='post_comments'
    )
    comment = models.CharField(max_length=300, null=True)

    contentType = models.CharField(
        max_length=50,
        choices=ContentType.choices,
        default=ContentType.MARKDOWN)

    published = models.DateTimeField(auto_now_add=True)
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="commentsSrc")
    remote_author = models.JSONField(default=dict, null=True, blank=True)

class Like(models.Model):
    summary = models.CharField(max_length=300)
    type = models.CharField(max_length=50, default='Like')
    author = models.ForeignKey(Author, on_delete=models.CASCADE, null=True, blank=True)
    remote_author = models.JSONField(default=dict, null=True, blank=True)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="likes")
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name="likes", null=True, blank=True)
    object = models.CharField(default=str, max_length=2048)
