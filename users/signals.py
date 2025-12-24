from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.contrib.auth import user_logged_in, user_logged_out
from .models import UserActivity, Profile, UserStat
from posts.models import Post, Comment, Like
import logging

logger = logging.getLogger(__name__)

_updating_stats = False

@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    UserActivity.objects.create(
        user=user,
        activity_type='login',
        details=f'Вход в систему с IP: {get_client_ip(request)}',
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )
    logger.info(f'User {user.username} logged in from {get_client_ip(request)}')

@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    if user and user.is_authenticated:
        UserActivity.objects.create(
            user=user,
            activity_type='logout',
            details=f'Выход из системы',
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        logger.info(f'User {user.username} logged out')

@receiver(post_save, sender=Post)
def log_post_creation(sender, instance, created, **kwargs):
    if created:
        UserActivity.objects.create(
            user=instance.author,
            activity_type='create_post',
            details=f'Создал(а) новость: "{instance.title}"',
            ip_address='',
            user_agent=''
        )

        update_user_stats(instance.author)

@receiver(post_save, sender=Comment)
def log_comment_creation(sender, instance, created, **kwargs):
    if created:
        UserActivity.objects.create(
            user=instance.user,
            activity_type='comment',
            details=f'Прокомментировал(а) новость: "{instance.post.title}"',
            ip_address='',
            user_agent=''
        )
        
        update_user_stats(instance.user)

@receiver(post_save, sender=Like)
def log_like_activity(sender, instance, created, **kwargs):
    if created:
        activity_type = 'like' if instance.is_like else 'dislike'
        UserActivity.objects.create(
            user=instance.user,
            activity_type=activity_type,
            details=f'Поставил(а) {activity_type} новости: "{instance.post.title}"',
            ip_address='',
            user_agent=''
        )

        update_user_stats(instance.user)

        update_user_stats(instance.post.author)

@receiver(post_delete, sender=Like)
def log_like_removal(sender, instance, **kwargs):
    update_user_stats(instance.user)
    update_user_stats(instance.post.author)

def update_user_stats(user):
    global _updating_stats
    
    if _updating_stats:
        return
    
    try:
        _updating_stats = True
        
        if hasattr(user, 'stats'):
            user.stats.update_stats()
    finally:
        _updating_stats = False

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip