from rest_framework import serializers
from .models import Category, Post
from author_manager.models import Author

class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = '__all__'


class PostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ['type', 'title', 'id', 'source', 'origin', 'description', 'content_type',
                    'content', 'author', 'categories', 'published', 'visibility', 'unlisted']
    
    # def to_representation(self, instance):
    #     data =  super().to_representation(instance)
    #     data['author'] = AuthorSerializer(Author.objects.get(pk=data['author'])).data
    #     return data