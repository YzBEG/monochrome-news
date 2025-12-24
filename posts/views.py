from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from .models import Post, Like, Comment
from .forms import PostForm, CommentForm
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken
import json
import logging

logger = logging.getLogger(__name__)


def get_jwt_user(request):
    jwt_auth = JWTAuthentication()
    
    try:
        header = jwt_auth.get_header(request)
        if header:
            raw_token = jwt_auth.get_raw_token(header)
            validated_token = jwt_auth.get_validated_token(raw_token)
            return jwt_auth.get_user(validated_token)
    except (InvalidToken, AttributeError, KeyError):
        pass
    
    try:
        auth_cookie = request.COOKIES.get('access_token')
        if auth_cookie:
            validated_token = jwt_auth.get_validated_token(auth_cookie)
            return jwt_auth.get_user(validated_token)
    except (InvalidToken, AttributeError, KeyError):
        pass
    
    return None


def post_list(request):
    posts = Post.objects.filter(is_published=True).order_by('-created_at')
    return render(request, 'posts/list.html', {'posts': posts})


@login_required
def create_post(request):
    if not request.user.is_authenticated:
        return redirect('/login/?next=/posts/create/')
    
    form = PostForm()
    return render(request, 'posts/create.html', {'form': form})


@csrf_exempt
def api_create_post(request):
    logger.info(f"API create post called. Method: {request.method}")
    
    user = get_jwt_user(request)
    if not user or not user.is_authenticated:
        logger.warning(f"Unauthorized attempt to create post")
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    logger.info(f"User: {user.username}")
    
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = user
            post.save()
            logger.info(f"Post created successfully: {post.id} - {post.title}")
            return JsonResponse({
                'success': True,
                'message': 'Новость успешно создана',
                'redirect_url': f'/posts/{post.id}/'
            })
        else:
            logger.error(f"Form errors: {form.errors}")
            return JsonResponse({
                'success': False,
                'message': 'Ошибка при создании новости',
                'errors': form.errors
            }, status=400)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id, is_published=True)
    comments = post.comments.all().order_by('-created_at')
    
    user_reaction = None
    if request.user.is_authenticated:
        reaction = Like.objects.filter(post=post, user=request.user).first()
        user_reaction = reaction.is_like if reaction else None
    
    return render(request, 'posts/detail.html', {
        'post': post,
        'comments': comments,
        'user_reaction': user_reaction,
        'likes_count': post.likes_count(),
        'dislikes_count': post.dislikes_count(),
    })


@csrf_exempt
def api_delete_post(request, post_id):
    user = get_jwt_user(request)
    if not user or not user.is_authenticated:
        return JsonResponse({
            'success': False,
            'error': 'Требуется авторизация'
        }, status=401)
    
    try:
        post = Post.objects.get(id=post_id)
    except Post.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Новость не найдена'
        }, status=404)
    
    if user != post.author and not user.is_staff:
        return JsonResponse({
            'success': False,
            'error': 'У вас нет прав для удаления этой новости'
        }, status=403)
    
    if request.method == 'DELETE':
        try:
            from users.models import UserActivity
            UserActivity.objects.create(
                user=user,
                activity_type='delete_post',
                details=f'Удалил(а) новость: "{post.title}"',
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            post_title = post.title
            post.delete()
            
            return JsonResponse({
                'success': True,
                'message': f'Новость "{post_title}" успешно удалена',
                'redirect_url': reverse('post_list')
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Ошибка при удалении: {str(e)}'
            }, status=500)
    
    return JsonResponse({
        'success': False,
        'error': 'Метод не разрешен'
    }, status=405)


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


@csrf_exempt
def like_post(request, post_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    user = get_jwt_user(request)
    if not user or not user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    post = get_object_or_404(Post, id=post_id)
    
    try:
        data = json.loads(request.body)
        reaction_type = data.get('reaction')
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    
    existing_reaction = Like.objects.filter(user=user, post=post).first()
    
    if existing_reaction:
        if (existing_reaction.is_like and reaction_type == 'like') or \
           (not existing_reaction.is_like and reaction_type == 'dislike'):
            existing_reaction.delete()
            liked = False
            disliked = False
        else:
            existing_reaction.is_like = (reaction_type == 'like')
            existing_reaction.save()
            liked = (reaction_type == 'like')
            disliked = not liked
    else:
        Like.objects.create(
            user=user,
            post=post,
            is_like=(reaction_type == 'like')
        )
        liked = (reaction_type == 'like')
        disliked = not liked
    
    return JsonResponse({
        'success': True,
        'likes': post.likes_count(),
        'dislikes': post.dislikes_count(),
        'liked': liked,
        'disliked': disliked,
    })


@csrf_exempt
def add_comment(request, post_id):
    logger.info(f"=== ADD COMMENT REQUEST ===")
    logger.info(f"Method: {request.method}")
    logger.info(f"Path: {request.path}")
    logger.info(f"Content-Type: {request.content_type}")
    logger.info(f"Headers: {dict(request.headers)}")
    
    if request.method != 'POST':
        logger.error("Method not allowed")
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    user = get_jwt_user(request)
    logger.info(f"User from JWT: {user} (authenticated: {user.is_authenticated if user else False})")
    
    if not user or not user.is_authenticated:
        logger.error("Authentication required")
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    try:
        post = Post.objects.get(id=post_id, is_published=True)
        logger.info(f"Post found: {post.title}")
    except Post.DoesNotExist:
        logger.error(f"Post not found: {post_id}")
        return JsonResponse({'error': 'Post not found'}, status=404)
    
    try:
        body = request.body.decode('utf-8') if request.body else 'Empty body'
        logger.info(f"Request body: {body[:500]}...")
        
        if request.content_type == 'application/json':
            data = json.loads(request.body)
            content = data.get('content', '').strip()
            logger.info(f"Content from JSON: {content[:100]}...")
        else:
            content = request.POST.get('content', '').strip()
            logger.info(f"Content from FormData: {content[:100]}...")
        
        if not content:
            logger.error("Empty content")
            return JsonResponse({'error': 'Comment content is required'}, status=400)
        
        if len(content) > 1000:
            logger.error(f"Content too long: {len(content)} chars")
            return JsonResponse({'error': 'Comment is too long (max 1000 chars)'}, status=400)

        comment = Comment.objects.create(
            user=user,
            post=post,
            content=content
        )
        logger.info(f"Comment created: ID {comment.id}")
        
        comment_html = f'''
            <div class="comment" style="animation: fadeIn 0.5s ease;">
                <div class="comment-header">
                    <span class="comment-author">
                        <a href="/users/{user.username}/" style="color: inherit; text-decoration: none;">
                            {user.username}
                        </a>
                    </span>
                    <span class="comment-date">{comment.created_at.strftime("%d.%m.%Y %H:%M")}</span>
                </div>
                <div class="comment-content">
                    {comment.content}
                </div>
            </div>
        '''
        
        response_data = {
            'success': True,
            'message': 'Комментарий добавлен',
            'comment_html': comment_html,
            'comments_count': post.comments_count(),
        }
        
        logger.info(f"Returning success response")
        return JsonResponse(response_data)
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {str(e)}")
        return JsonResponse({'error': f'Invalid JSON format: {str(e)}'}, status=400)
    except Exception as e:
        logger.error(f"Server error: {str(e)}", exc_info=True)
        return JsonResponse({'error': f'Server error: {str(e)}'}, status=500)