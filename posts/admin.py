from django.contrib import admin
from .models import Post, Like, Comment

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'created_at', 'is_published', 'likes_count', 'dislikes_count', 'comments_count']
    list_filter = ['is_published', 'created_at']
    search_fields = ['title', 'content', 'author__username']
    list_editable = ['is_published']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('title', 'content', 'image')
        }),
        ('Автор и даты', {
            'fields': ('author', 'created_at', 'updated_at')
        }),
        ('Публикация', {
            'fields': ('is_published',)
        }),
    )


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ['user', 'post', 'is_like', 'created_at']
    list_filter = ['is_like', 'created_at']
    search_fields = ['user__username', 'post__title']
    readonly_fields = ['created_at']


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['user', 'post', 'content_short', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'post__title', 'content']
    readonly_fields = ['created_at', 'updated_at']
    
    def content_short(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_short.short_description = 'Комментарий'