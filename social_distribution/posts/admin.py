from django.contrib import admin
from .models import *
import nested_admin
# Register your models here.

admin.site.register(Category)
admin.site.register(Post)
# admin.site.register(Comment)