from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from news_site import views as news_views
from users import views as user_views
from users.api_views import RegisterAPIView, LoginAPIView, LogoutAPIView, RefreshTokenAPIView, HeartbeatAPIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', news_views.home, name='home'),
    
    path('login/', user_views.login_page, name='login'),
    path('register/', user_views.register_page, name='register'),
    path('users/<str:username>/', user_views.profile, name='profile'),

    path('api/register/', RegisterAPIView.as_view(), name='api_register'),
    path('api/login/', LoginAPIView.as_view(), name='api_login'),
    path('api/logout/', LogoutAPIView.as_view(), name='api_logout'),
    path('api/token/refresh/', RefreshTokenAPIView.as_view(), name='api_token_refresh'),
    path('api/heartbeat/', HeartbeatAPIView.as_view(), name='api_heartbeat'),

    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    path('posts/', include('posts.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)