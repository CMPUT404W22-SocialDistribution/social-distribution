from django.urls import path, url
from .views import *

app_name = 'posts'
urlpatterns = [
    url(r'^authors/<str:author_id>/posts/$', PostsAPI.as_view(), name ="posts"),
  
]