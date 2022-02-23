from django.urls import path, re_path
from .views import *

app_name = 'posts'
urlpatterns = [
    path('api/authors/<str:author_id>/posts/', MyPostsAPI.as_view(), name ="my_posts_api"),
    path('search/', SearchView.as_view(), name="search"),
    path('authors/<str:author_id>/posts/',my_posts, name ="posts"),
    path('authors/<str:author_id>/posts/create', post_create, name ="post_create"),
    path('authors/<str:author_id>/posts/<str:post_id>/edit', post_edit, name ="post_edit"),
    path('authors/<str:author_id>/posts/<str:post_id>', post_detail, name ="post_detail"),
    path('authors/<str:author_id>/posts/<str:post_id>/delete', post_delete, name ="post_delete"),
    path('api/posts/', PostsAPI.as_view(), name="all_posts_api"),
]