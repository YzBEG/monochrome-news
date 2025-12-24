from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from posts.models import Post
from .models import UserActivity, Profile
import json


def login_page(request):
    return render(request, 'users/login.html')


def register_page(request):
    return render(request, 'users/register.html')


def profile(request, username):
    try:
        profile_user = User.objects.get(username=username)
        
        if request.user.is_authenticated and request.user != profile_user:
            UserActivity.objects.create(
                user=request.user,
                activity_type='view_profile',
                details=f'Просмотр профиля пользователя {profile_user.username}',
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )

        user_posts = Post.objects.filter(author=profile_user, is_published=True).order_by('-created_at')

        is_owner = request.user.is_authenticated and request.user == profile_user
        
    except User.DoesNotExist:
        return redirect('home')
    
    return render(request, 'users/profile.html', {
        'profile_user': profile_user,
        'user_posts': user_posts,
        'is_owner': is_owner
    })


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip