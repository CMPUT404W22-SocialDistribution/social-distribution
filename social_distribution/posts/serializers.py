from urllib import response
from rest_framework import serializers
from .models import Category, Post, Comment 
from author_manager.models import Author

class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = '__all__'


class PostSerializer(serializers.ModelSerializer):
    author_username = serializers.SerializerMethodField('get_author_username')
    author_displayName = serializers.SerializerMethodField('get_author_displayName')
    author_image = serializers.SerializerMethodField('get_author_image')

    def get_author_image(self, obj):
        return obj.author.profileImage

    def get_author_username(self, obj):
        return obj.author.user.username
    
    def get_author_displayName(self, obj):
        return obj.author.displayName

    #add comments, like,...
    class Meta:
        model = Post
        fields = ['type', 'author_username', 'author_displayName', 'title', 'id', 'source', 'origin', 'description', 'content_type',
                    'content', 'author', 'categories', 'published', 'visibility', 'unlisted', 'author_image', 'image']
    
    # def to_representation(self, instance):
    #     data =  super().to_representation(instance)
    #     data['author'] = AuthorSerializer(Author.objects.get(pk=data['author'])).data
    #     return data

        
class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ['type', 'author', 'comment', 'contentType', 'published', 'id']

    def __init__(self, *args, **kwargs):
        remove_fields = kwargs.pop('remove_fields', None)
        super(CommentSerializer, self).__init__(*args, **kwargs)

        if remove_fields:
            for field in remove_fields:
                self.fields.pop(field)
