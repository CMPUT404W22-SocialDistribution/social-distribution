from rest_framework import serializers
from .models import Author


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = ['user','uuid', 'type', 'id', 'host', 'displayName', 'url', 'github', 'profileImage']

    def __init__(self, *args, **kwargs):
        remove_fields = kwargs.pop('remove_fields', None)
        super(ProfileSerializer, self).__init__(*args, **kwargs)

        if remove_fields:
            for field in remove_fields:
                self.fields.pop(field)