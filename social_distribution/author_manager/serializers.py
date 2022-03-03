from dataclasses import fields
from os import remove
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
    
    def to_representation(self, instance):
        response =  super().to_representation(instance)
        if "actor" in response:
            actor = response["actor"]
            author= Author.objects.get(id=actor)
        response["actor"] = ProfileSerializer(author, remove_fields=['user']).data

        if "object" in response:
            object = response["object"]
            author= Author.objects.get(id=object)
        response["object"] = ProfileSerializer(author, remove_fields=['user']).data
        
        return response