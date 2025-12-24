from django.urls import path
from . import views

app_name = 'news_site'

urlpatterns = [
    path('', views.home, name='home'),
]