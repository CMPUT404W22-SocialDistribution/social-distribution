from django.contrib import admin
from . import models
from .models import Author
import nested_admin

class AuthorAdmin(nested_admin.NestedModelAdmin):
    list_display = ('user', 'id', 'host', 'displayName', 'github')
    models = models.Author



admin.site.register(models.Author, AuthorAdmin)