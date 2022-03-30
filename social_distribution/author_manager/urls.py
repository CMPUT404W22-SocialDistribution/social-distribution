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
    path('api/authors/<uuid:id>', ProfileAPI.as_view(), name='author'),
    path('authors/<uuid:id>/', get_profile, name='profile'),
    path('api/authors', GetAllAuthors.as_view(), name='getAllAuthors'),
    path('authors/<uuid:id>/edit', views.profile_edit, name='editProfile'),
    path('authors/<uuid:author_id>/friends', friends_view, name="friends"),
    path('search/authors', SearchAuthorView.as_view(), name="search_author"),
    path('api/authors/<uuid:author_id>/followers/<uuid:follower_id>', FriendDetailAPI.as_view(), name="friend_detail_api"),
    path('authors/<uuid:id>/inbox', inbox_view, name="inbox"),
    path('api/authors/<uuid:id>/inbox', InboxAPI.as_view(), name='inbox_api'),
    path('api/node/authors/<uuid:author_id>/inbox', RemoteInboxAPI.as_view(), name='remote_inbox_api'),
    path('api/authors/<uuid:id>/followers', FriendsAPI.as_view(), name='friends_api'),
    path('api/authors/<uuid:id>/remotefriends', RemoteFriendsAPI.as_view(), name='remotefriends_api'),
    path('api/friendrequests', FriendRequestsAPI.as_view(), name='friendrequests_api'),
    path('api/authors/<uuid:author_id>/liked', AuthorLikedAPI.as_view(), name='author_liked_api')
]
