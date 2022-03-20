from django.contrib import admin

from .models import *

class PostAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'source', 'origin', 'content_type', 'content', 'visibility')
# Register your models here.
admin.site.register(Category)
admin.site.register(Post, PostAdmin)
admin.site.register(Comment)
admin.site.register(Like)
