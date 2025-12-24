from django.contrib import admin
from django.utils.html import format_html
from .models import Profile, UserActivity, UserStat

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'get_online_status', 'created_at', 'last_seen']
    list_filter = ['created_at', 'last_seen']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['created_at', 'last_seen', 'last_activity']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('user', 'bio', 'avatar', 'birth_date', 'website')
        }),
        ('Статистика', {
            'fields': ('created_at', 'last_seen', 'last_activity')
        }),
    )
    
    def get_online_status(self, obj):
        return format_html(obj.get_online_status())
    get_online_status.short_description = 'Статус'


@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    list_display = ['user', 'activity_type', 'ip_address', 'created_at']
    list_filter = ['activity_type', 'created_at']
    search_fields = ['user__username', 'details', 'ip_address']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('user', 'activity_type', 'details')
        }),
        ('Техническая информация', {
            'fields': ('ip_address', 'user_agent', 'created_at')
        }),
    )


@admin.register(UserStat)
class UserStatAdmin(admin.ModelAdmin):
    list_display = ['user', 'total_posts', 'total_comments', 'total_likes_given', 
                    'total_likes_received', 'last_updated']
    list_filter = ['last_updated']
    search_fields = ['user__username']
    readonly_fields = ['last_updated']
    
    fieldsets = (
        ('Статистика активности', {
            'fields': ('total_posts', 'total_comments')
        }),
        ('Реакции (поставленные)', {
            'fields': ('total_likes_given', 'total_dislikes_given')
        }),
        ('Реакции (полученные)', {
            'fields': ('total_likes_received', 'total_dislikes_received')
        }),
        ('Техническая информация', {
            'fields': ('last_updated',)
        }),
    )
    
    actions = ['update_stats_action']
    
    def update_stats_action(self, request, queryset):
        for stat in queryset:
            stat.update_stats()
        self.message_user(request, f"Статистика обновлена для {queryset.count()} пользователей")
    update_stats_action.short_description = "Обновить статистику"