from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.core.cache import cache
from datetime import timedelta

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(max_length=500, blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    birth_date = models.DateField(null=True, blank=True)
    website = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(auto_now=True)
    last_activity = models.DateTimeField(auto_now=True)
    
    def update_activity(self):
        from django.utils import timezone
        self.last_activity = timezone.now()
        self.last_seen = timezone.now()
        self.save(update_fields=['last_activity', 'last_seen'])
    
    def is_online(self):
        from django.utils import timezone
        from datetime import timedelta
        
        if self.last_activity:
            now = timezone.now()
            return now <= self.last_activity + timedelta(minutes=5)
        return False
    
    def get_online_status_display(self):
        if self.is_online():
            return '<span style="color: #4CAF50;"><i class="fas fa-circle"></i> Онлайн</span>'
        else:
            last_seen = self.last_seen.strftime('%d.%m.%Y %H:%M') if self.last_seen else 'никогда'
            return f'<span style="color: #888;"><i class="far fa-circle"></i> Был(а) {last_seen}</span>'
    
    def get_post_count(self):
        from posts.models import Post
        return Post.objects.filter(author=self.user, is_published=True).count()
    
    def get_comment_count(self):
        from posts.models import Comment
        return Comment.objects.filter(user=self.user).count()
    
    def get_like_count(self):
        from posts.models import Like
        return Like.objects.filter(user=self.user, is_like=True).count()
    
    def get_dislike_count(self):
        from posts.models import Like
        return Like.objects.filter(user=self.user, is_like=False).count()
    
    def get_total_activity(self):
        return self.get_post_count() + self.get_comment_count()
    
    def get_recent_activity(self, limit=10):
        from posts.models import Post, Comment
        from datetime import datetime, timedelta
        
        activities = []
        
        posts = Post.objects.filter(author=self.user, is_published=True).order_by('-created_at')[:limit]
        for post in posts:
            activities.append({
                'type': 'post',
                'object': post,
                'time': post.created_at,
                'message': f'Опубликовал(а) новость: "{post.title}"'
            })
        
        comments = Comment.objects.filter(user=self.user).order_by('-created_at')[:limit]
        for comment in comments:
            activities.append({
                'type': 'comment',
                'object': comment,
                'time': comment.created_at,
                'message': f'Прокомментировал(а) новость: "{comment.post.title}"'
            })
        
        activities.sort(key=lambda x: x['time'], reverse=True)
        return activities[:limit]
    
    def __str__(self):
        return f'{self.user.username} Profile'


class UserActivity(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    activity_type = models.CharField(max_length=50, choices=[
        ('login', 'Вход в систему'),
        ('logout', 'Выход из системы'),
        ('view_post', 'Просмотр новости'),
        ('create_post', 'Создание новости'),
        ('like', 'Лайк'),
        ('dislike', 'Дизлайк'),
        ('comment', 'Комментарий'),
        ('view_profile', 'Просмотр профиля'),
    ])
    details = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Активность пользователя'
        verbose_name_plural = 'Активности пользователей'
    
    def __str__(self):
        return f'{self.user.username} - {self.get_activity_type_display()} - {self.created_at.strftime("%d.%m.%Y %H:%M")}'


class UserStat(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='stats')
    total_posts = models.IntegerField(default=0)
    total_comments = models.IntegerField(default=0)
    total_likes_given = models.IntegerField(default=0)
    total_dislikes_given = models.IntegerField(default=0)
    total_likes_received = models.IntegerField(default=0)
    total_dislikes_received = models.IntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Статистика пользователя'
        verbose_name_plural = 'Статистика пользователей'
    
    def update_stats(self):
        from posts.models import Post, Comment, Like
        
        self.total_posts = Post.objects.filter(author=self.user, is_published=True).count()
        self.total_comments = Comment.objects.filter(user=self.user).count()

        self.total_likes_given = Like.objects.filter(user=self.user, is_like=True).count()
        self.total_dislikes_given = Like.objects.filter(user=self.user, is_like=False).count()
        
        user_posts = Post.objects.filter(author=self.user)
        self.total_likes_received = Like.objects.filter(post__in=user_posts, is_like=True).count()
        self.total_dislikes_received = Like.objects.filter(post__in=user_posts, is_like=False).count()

        self.save(update_fields=[
            'total_posts', 'total_comments',
            'total_likes_given', 'total_dislikes_given',
            'total_likes_received', 'total_dislikes_received',
            'last_updated'
        ])
    
    def __str__(self):
        return f'Статистика: {self.user.username}'

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
        UserStat.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()