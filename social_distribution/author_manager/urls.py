from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from .views import ProfileAPI, GetAllAuthors
app_name = 'author_manager'
urlpatterns = [
    path('signup/', views.sign_up, name ="sign_up"),
    path('login/', views.sign_in, name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='author_manager:login'), name='logout'),
    path('home/', views.home, name='home'),
    path('authors/<uuid:id>/',  ProfileAPI.as_view(), name='profile'),
    path('authors/', GetAllAuthors.as_view(), name='getAllAuthors'),

]