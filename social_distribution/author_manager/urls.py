from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from .views import *

app_name = 'author_manager'
urlpatterns = [
    path('signup/', views.sign_up, name ="sign_up"),
    path('login/', views.sign_in, name='login'),
    path('', views.home, name='home'),
    path('github/', views.github_events, name='github'),
    path('logout/', views.sign_out, name='logout'),
    path('authors/<str:id>/',  ProfileAPI.as_view(), name='profile'),
    path('authors/', GetAllAuthors.as_view(), name='getAllAuthors'),
    path('authors/<str:id>/edit', views.profile_edit, name='editProfile'),
    path('authors/<str:author_id>/friends', friends_view, name ="friends"),
    path('authors/<str:author_id>/inbox', inbox_view, name = "inbox"),
]