from rest_framework import serializers

from author_manager.models import Author
from .models import Post, Comment, Like


class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = ['id', 'type', 'host', 'displayName', 'github', 'profileImage', 'url']


class PostSerializer(serializers.ModelSerializer):
    author_username = serializers.SerializerMethodField('get_author_username')
    author_displayName = serializers.SerializerMethodField('get_author_displayName')
    author_image = serializers.SerializerMethodField('get_author_image')
    comments = serializers.SerializerMethodField('get_comments_url')
    num_likes = serializers.SerializerMethodField('get_num_likes')

    def get_author_image(self, obj):
        return obj.author.profileImage

    def get_author_username(self, obj):
        return obj.author.user.username

    def get_author_displayName(self, obj):
        return obj.author.displayName

    def get_comments_url(self, obj):
        return obj.author.host + 'api/' + 'authors/' + str(obj.author.id) + '/posts/' + str(obj.id) + '/comments'

    def get_num_likes(self, obj):
        return Like.objects.filter(post__id__exact=obj.id, comment__id__isnull=True).count()

    # add comments, like,...
    class Meta:
        model = Post
        fields = ['type', 'author_username', 'author_displayName', 'title', 'id', 'source', 'origin', 'description',
                  'content_type', 'visibleTo', 'unlisted',
                  'content', 'author', 'categories', 'published', 'visibility', 'unlisted', 'author_image', 'image',
                  'comments', 'commentsSrc', 'num_likes']

    # def to_representation(self, instance):
    #     data =  super().to_representation(instance)
    #     data['author'] = AuthorSerializer(Author.objects.get(pk=data['author'])).data
    #     return data
    def to_representation(self, instance):
        response = super().to_representation(instance)
        if "author" in response:
            post_author = response["author"]
            author = Author.objects.get(id=post_author)

        response["author"] = AuthorSerializer(author).data

        if "commentsSrc" in response:
            comments = response["commentsSrc"]
            for i in range(len(comments)):
                post_comment = Comment.objects.get(id=comments[i])
                comments[i] = CommentSerializer(post_comment).data

            data = {
                "type": "comments",
                "size": len(comments),
                "comments": comments[::-1],
            }
            response["commentsSrc"] = data
        return response


class CommentSerializer(serializers.ModelSerializer):
    author_displayName = serializers.SerializerMethodField('get_author_displayName')
    num_likes = serializers.SerializerMethodField('get_num_likes')

    def get_author_displayName(self, obj):
        return obj.author.displayName

    def get_num_likes(self, obj):
        return Like.objects.filter(comment__id__exact=obj.id).count()

    class Meta:
        model = Comment
        fields = ['type', 'author', 'author_displayName', 'comment', 'contentType', 'published', 'id', 'num_likes']

    def __init__(self, *args, **kwargs):
        remove_fields = kwargs.pop('remove_fields', None)
        super(CommentSerializer, self).__init__(*args, **kwargs)

        if remove_fields:
            for field in remove_fields:
                self.fields.pop(field)

    def to_representation(self, instance):
        response = super().to_representation(instance)
        if "author" in response:
            comment_author = response["author"]
            author = Author.objects.get(id=comment_author)
        response["author"] = AuthorSerializer(author).data
        return response


class LikeSerializer(serializers.ModelSerializer):
    object = serializers.SerializerMethodField('get_object')

    class Meta:
        model = Like
        fields = ['summary', 'type', 'author', 'post', 'comment', 'object']

    @staticmethod
    def get_context():
        return "https://www.w3.org/ns/activitystreams"

    @staticmethod
    def get_object(obj):
        return obj.author.host + '/'.join(['api', 'authors', str(obj.author.id), 'posts', str(obj.post.id)])

    def to_representation(self, instance):
        response = super().to_representation(instance)
        response['@context'] = self.get_context()
        author = Author.objects.get(id=response['author'])
        response['author'] = AuthorSerializer(author).data
        return response
