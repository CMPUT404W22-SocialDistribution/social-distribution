from dataclasses import fields
from rest_framework import serializers
from .models import Author, FriendRequest


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = ['user', 'type', 'id', 'host', 'displayName', 'url', 
                'github', 'profileImage', 'birthday', 'email', 'about']

    def __init__(self, *args, **kwargs):
        remove_fields = kwargs.pop('remove_fields', None)
        super(ProfileSerializer, self).__init__(*args, **kwargs)

        if remove_fields:
            for field in remove_fields:
                self.fields.pop(field)

class FriendRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = FriendRequest
        fields = '__all__'
