from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, AuthenticationFailed
from django.utils.functional import SimpleLazyObject
import jwt


class JWTAuthenticationMiddleware(MiddlewareMixin):

    def process_request(self, request):
        request.user = SimpleLazyObject(lambda: self.get_user_from_jwt(request))
    
    def get_user_from_jwt(self, request):
        jwt_auth = JWTAuthentication()
        access_token = request.COOKIES.get('access_token')
        if access_token:
            try:
                validated_token = jwt_auth.get_validated_token(access_token)
                user = jwt_auth.get_user(validated_token)
                if user and user.is_authenticated:
                    return user
            except (InvalidToken, AuthenticationFailed, jwt.exceptions.DecodeError):
                pass
        
        try:
            header = jwt_auth.get_header(request)
            if header is not None:
                raw_token = jwt_auth.get_raw_token(header)
                validated_token = jwt_auth.get_validated_token(raw_token)
                user = jwt_auth.get_user(validated_token)
                if user and user.is_authenticated:
                    return user
        except (InvalidToken, AuthenticationFailed, AttributeError, KeyError):
            pass
        
        return AnonymousUser()
    def process_response(self, request, response):
        if hasattr(request, 'user') and request.user.is_authenticated:
            try:
                from .models import Profile
                profile = request.user.profile
                profile.update_activity()
            except (Profile.DoesNotExist, AttributeError):
                pass
        
        return response