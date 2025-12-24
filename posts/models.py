from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse


class Post(models.Model):
    title = models.CharField(max_length=200, verbose_name="Заголовок")
    content = models.TextField(verbose_name="Содержание")
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Автор")
    image = models.ImageField(upload_to='posts/', blank=True, null=True, verbose_name="Изображение")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    is_published = models.BooleanField(default=True, verbose_name="Опубликовано")
    
    def likes_count(self):
        return self.likes.filter(is_like=True).count()
    
    def dislikes_count(self):
        return self.likes.filter(is_like=False).count()
    
    def comments_count(self):
        return self.comments.count()
    
    def user_reaction(self, user):
        if user.is_authenticated:
            reaction = self.likes.filter(user=user).first()
            return reaction.is_like if reaction else None
        return None
    
    def can_delete(self, user):
        return user.is_authenticated and (user == self.author or user.is_staff)
    
    
    def get_delete_url(self):
        return reverse('api_post_delete', args=[self.id])
    
    
    def __str__(self):
        return self.title
    
    class Meta:
        ordering = ['-created_at']
        permissions = [
            ("delete_any_post", "Может удалять любые посты"),
        ]


class Like(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='post_likes')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='likes')
    is_like = models.BooleanField(default=True) 
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'post']
        verbose_name = 'Реакция'
        verbose_name_plural = 'Реакции'
    
    def __str__(self):
        reaction = "Лайк" if self.is_like else "Дизлайк"
        return f"{self.user.username} - {reaction} на '{self.post.title}'"


class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='post_comments')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField(verbose_name="Текст комментария")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'
    
    def __str__(self):
        return f"Комментарий от {self.user.username} к '{self.post.title}'"