from django.contrib import admin
from .models import *
import nested_admin

class AuthorAdmin(nested_admin.NestedModelAdmin):
    list_display = ('user', 'id', 'host', 'displayName', 'github')
    models = Author



admin.site.register(Author, AuthorAdmin)
admin.site.register(FollowerList)
admin.site.register(FriendRequest)
admin.site.register(Inbox)