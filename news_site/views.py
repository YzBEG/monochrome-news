from django.shortcuts import render
from posts.models import Post

def home(request):
    latest_posts = Post.objects.filter(is_published=True).order_by('-created_at')[:3]
    return render(request, 'home.html', {'posts': latest_posts})