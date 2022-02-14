from django.contrib import admin
from . import models
from .models import Author

admin.site.register(models.Author)