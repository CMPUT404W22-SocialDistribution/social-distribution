from django.urls import path

from . import views
from .views import *

app_name = 'author_manager'
urlpatterns = [
    path('signup/', views.sign_up, name="sign_up"),
    path('login/', views.sign_in, name='login'),
    path('', views.home, name='home'),
    path('github/', views.github_events, name='github'),
    path('logout/', views.sign_out, name='logout'),
    path('api/authors/<str:id>/', ProfileAPI.as_view(), name='author'),
    path('authors/<str:id>/', get_profile, name='profile'),
    path('api/authors/', GetAllAuthors.as_view(), name='getAllAuthors'),
    path('authors/<str:id>/edit', views.profile_edit, name='editProfile'),
    path('authors/<str:author_id>/friends', friends_view, name="friends"),
    path('search/authors', SearchAuthorView.as_view(), name="search_author"),
    path('authors/<str:id>/inbox', inbox_view, name="inbox"),
    path('api/authors/<str:id>/inbox', InboxAPI.as_view(), name='inbox_api'),
    path('api/authors/<str:id>/friends', FriendsAPI.as_view(), name='friends_api'),
    path('api/friendrequests', FriendRequestsAPI.as_view(), name='friendrequests_api'),
    # path('api/authors/<str:author_id>/inbox', LikeAPI.as_view(), name='like_api'),
    path('api/authors/<str:author_id>/liked', AuthorLikedAPI.as_view(), name='author_liked_api')
]
