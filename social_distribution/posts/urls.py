from django.urls import path, re_path
from .views import *

app_name = 'posts'
urlpatterns = [
    path('authors/<str:author_id>/posts/', PostsAPI.as_view(), name ="posts"),
  
]