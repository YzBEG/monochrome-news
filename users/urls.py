from django.urls import path
from . import views
from .api_views import RegisterAPIView, LoginAPIView

app_name = 'users' 

urlpatterns = [
    path('login/', views.user_login, name='login'), 
    path('logout/', views.user_logout, name='logout'),  
    path('register/', views.register, name='register'),  
    path('<str:username>/', views.profile, name='profile'),  
    path('api/register/', RegisterAPIView.as_view(), name='api_register'),
    path('api/login/', LoginAPIView.as_view(), name='api_login'),
]