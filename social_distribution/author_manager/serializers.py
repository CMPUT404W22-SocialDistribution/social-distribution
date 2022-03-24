from rest_framework import serializers

from posts.models import Like
from .models import Author, FriendRequest, Inbox


class ProfileSerializer(serializers.ModelSerializer):
    username = serializers.SerializerMethodField('get_author_username')
    
    def get_author_username(self, obj):
        return obj.user.username

    class Meta:
        model = Author
        fields = ['user', 'type', 'id', 'host', 'username', 'displayName', 'url',
                  'github', 'profileImage', 'birthday', 'email', 'about']

    def __init__(self, *args, **kwargs):
        remove_fields = kwargs.pop('remove_fields', None)
        super(ProfileSerializer, self).__init__(*args, **kwargs)

        if remove_fields:
            for field in remove_fields:
                self.fields.pop(field)

class RemoteProfileSerializer(serializers.ModelSerializer):
    id = serializers.SerializerMethodField('get_author_id')

    def get_author_id(self, obj):
        return obj.url

    class Meta:
        model = Author
        fields = ['type', 'id', 'host', 'displayName', 'url',
                  'github', 'profileImage', 'birthday', 'email', 'about']


class FriendRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = FriendRequest
        fields = '__all__'

    def to_representation(self, instance):
        response = super().to_representation(instance)
        if "actor" in response:
            actor = response["actor"]
            author = Author.objects.get(id=actor)
            response["actor"] = ProfileSerializer(author, remove_fields=['user']).data

        if "object" in response:
            object = response["object"]
            author = Author.objects.get(id=object)
            response["object"] = ProfileSerializer(author, remove_fields=['user']).data

        return response


class LikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Like
        fields = '__all__'

    def to_representation(self, instance):
        response = super().to_representation(instance)
        return response

class InboxSerializer(serializers.ModelSerializer):
    class Meta:
        model = Inbox
        fields = ['item']  

        
