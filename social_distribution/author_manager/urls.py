from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
app_name = 'author_manager'
urlpatterns = [
    path('signup/', views.sign_up, name ="sign_up"),
    path('login/', views.sign_in, name='login'),
    path('home/', views.home, name='home'),
    path('logout/', views.sign_out, name='logout')

]