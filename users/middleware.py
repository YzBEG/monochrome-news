from django.utils import timezone
from .models import Profile, UserActivity
from django.utils.deprecation import MiddlewareMixin


class UserActivityMiddleware(MiddlewareMixin):
    
    def process_request(self, request):
        if hasattr(request, 'user') and request.user.is_authenticated:
            try:
                profile = request.user.profile
                profile.last_activity = timezone.now()
                profile.save(update_fields=['last_activity'])
                
                if request.path.startswith('/posts/') and request.path.count('/') == 2:
                    try:
                        from posts.models import Post
                        post_id = request.path.split('/')[2]
                        if post_id and post_id.isdigit():
                            post = Post.objects.get(id=int(post_id))
                            UserActivity.objects.create(
                                user=request.user,
                                activity_type='view_post',
                                details=f'Просмотр новости: {post.title}',
                                ip_address=self.get_client_ip(request),
                                user_agent=request.META.get('HTTP_USER_AGENT', '')
                            )
                    except:
                        pass
                        
            except (Profile.DoesNotExist, AttributeError):
                pass
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip