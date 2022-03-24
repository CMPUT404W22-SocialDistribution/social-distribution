from django.urls import path

from .views import MyPostsAPI, PostsAPI, PostImageAPI, SearchView, PostDetailAPI, my_posts, post_create, post_edit, \
    post_detail, post_share, post_delete, CommentsAPI, create_comment, create_remote_comment, PostLikesAPI, CommentLikesAPI, RemotePostsAPI

app_name = 'posts'
urlpatterns = [
    path('api/authors/<uuid:author_id>/posts/', MyPostsAPI.as_view(), name="my_posts_api"),
    path('search/', SearchView.as_view(), name="search"),
    path('authors/<uuid:author_id>/posts/', my_posts, name="posts"),
    path('authors/<uuid:author_id>/posts/create', post_create, name="post_create"),
    path('authors/<uuid:author_id>/posts/<uuid:post_id>/edit', post_edit, name="post_edit"),
    path('authors/<uuid:author_id>/posts/<uuid:post_id>', post_detail, name="post_detail"),
    path('authors/<uuid:author_id>/posts/<uuid:post_id>/delete', post_delete, name="post_delete"),
    path('authors/<uuid:author_id>/posts/<uuid:post_id>/share', post_share, name="post_share"),
    path('api/posts/', PostsAPI.as_view(), name="all_posts_api"),
    path('api/authors/<uuid:author_id>/posts/<uuid:post_id>/comments', CommentsAPI.as_view(), name="comments_api"),
    path('authors/<uuid:author_id>/posts/<uuid:post_id>/comments', create_comment, name="comments"),
    path('api/authors/<uuid:author_id>/posts/<uuid:post_id>/image', PostImageAPI.as_view(), name="post_image"),
    path('api/authors/<uuid:author_id>/posts/<uuid:post_id>', PostDetailAPI.as_view(), name="post_detail_api"),
    path('api/authors/<uuid:author_id>/posts/<uuid:post_id>/likes', PostLikesAPI.as_view(), name="post_likes_api"),
    path('api/authors/<uuid:author_id>/posts/<uuid:post_id>/comments/<str:comment_id>/likes', CommentLikesAPI.as_view(),
         name="comment_likes_api"),
    path('api/posts/remote', RemotePostsAPI, name='remote_posts_api'),
    path('<str:url>/authors/<uuid:author_id>/posts/<uuid:post_id>/comments', create_remote_comment, name='create_remote_comment')
]
