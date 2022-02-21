from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from .views import ProfileAPI, GetAllAuthors
app_name = 'author_manager'
urlpatterns = [
    path('signup/', views.sign_up, name ="sign_up"),
    path('login/', views.sign_in, name='login'),
    path('', views.home, name='home'),
    path('logout/', views.sign_out, name='logout'),
    path('authors/<uuid:id>/',  ProfileAPI.as_view(), name='profile'),
    path('authors/', GetAllAuthors.as_view(), name='getAllAuthors'),
]