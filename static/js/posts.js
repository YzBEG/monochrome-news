class PostService {
    constructor() {
        this.authService = window.authService;
    }
    

    initReactionButtons() {
        document.querySelectorAll('.reaction-btn').forEach(button => {
            button.addEventListener('click', (e) => this.handleReaction(e));
        });
    }
    showMessage(text, type = 'info', duration = 3000) {
        if (window.showMonochromeMessage) {
            window.showMonochromeMessage(text, type, duration);
        } else if (this.authService && this.authService.showMessage) {
            this.authService.showMessage(text, type, duration);
        } else {
            const div = document.createElement('div');
            div.textContent = text;
            div.style.cssText = `
                position: fixed;
                top: 100px;
                right: 20px;
                padding: 12px 20px;
                background: ${type === 'error' ? 'rgba(0,0,0,0.95)' : 'rgba(255,255,255,0.95)'};
                color: ${type === 'error' ? '#fff' : '#000'};
                border: 1px solid rgba(255,255,255,0.2);
                border-radius: 0;
                z-index: 9999;
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                animation: slideInRight 0.3s ease;
                font-family: 'Segoe UI', sans-serif;
                font-size: 13px;
                letter-spacing: 1px;
                text-transform: uppercase;
            `;
            document.body.appendChild(div);
            
            setTimeout(() => {
                div.style.animation = 'slideOutRight 0.3s ease';
                setTimeout(() => div.remove(), 300);
            }, duration);
        }
    }
    async handleReaction(event) {
        const button = event.currentTarget;
        
        if (!this.authService.isAuthenticated()) {
            this.authService.showMessage('Для оценки необходимо войти в систему', 'error');
            return;
        }

        if (button.classList.contains('disabled')) {
            return;
        }
        
        const container = button.closest('.reaction-buttons');
        if (!container) return;
        
        const postId = container.dataset.postId;
        const reaction = button.dataset.reaction; 

        const originalHTML = button.innerHTML;
        button.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
        button.disabled = true;
        
        try {
            const response = await this.authService.authFetch(`/posts/${postId}/like/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ reaction: reaction })
            });
            
            const data = await response.json();
            
            if (response.ok && data.success) {
                this.updateReactionCounts(container, data.likes, data.dislikes);
                this.updateActiveReactions(container, data.liked, data.disliked);
                this.authService.showMessage('Спасибо за вашу оценку!', 'success');
            } else {
                this.authService.showMessage(data.error || 'Ошибка при оценке', 'error');
            }
        } catch (error) {
            console.error('Reaction error:', error);
            this.authService.showMessage('Ошибка сети', 'error');
        } finally {
            button.innerHTML = originalHTML;
            button.disabled = false;
        }
    }
    
    updateReactionCounts(container, likes, dislikes) {
        const likeCount = container.querySelector('.like-btn .reaction-count');
        const dislikeCount = container.querySelector('.dislike-btn .reaction-count');
        
        if (likeCount) likeCount.textContent = likes;
        if (dislikeCount) dislikeCount.textContent = dislikes;
        
        document.querySelectorAll(`[data-post-id="${container.dataset.postId}"] .like-count`).forEach(el => {
            el.textContent = likes;
        });
        
        document.querySelectorAll(`[data-post-id="${container.dataset.postId}"] .dislike-count`).forEach(el => {
            el.textContent = dislikes;
        });
    }
    
    updateActiveReactions(container, liked, disliked) {
        const likeBtn = container.querySelector('.like-btn');
        const dislikeBtn = container.querySelector('.dislike-btn');
        
        likeBtn?.classList.remove('active');
        dislikeBtn?.classList.remove('active');
        
        if (liked) {
            likeBtn?.classList.add('active');
        } else if (disliked) {
            dislikeBtn?.classList.add('active');
        }
    }
    
    initCommentForm() {
        const form = document.getElementById('comment-form');
        if (!form) return;
        
        form.addEventListener('submit', (e) => this.handleCommentSubmit(e));
        
        if (!this.authService.isAuthenticated()) {
            const textarea = form.querySelector('textarea');
            const submitBtn = form.querySelector('button[type="submit"]');
            
            if (textarea) {
                textarea.placeholder = 'Войдите чтобы оставить комментарий';
                textarea.disabled = true;
            }
            
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.textContent = 'Войдите чтобы комментировать';
            }
        }
    }

async handleCommentSubmit(event) {
    event.preventDefault();
    event.stopPropagation();
    
    const form = event.currentTarget;

    if (!this.authService.isAuthenticated()) {
        this.authService.showMessage('Для комментирования необходимо войти в систему', 'error');
        window.location.href = '/login/?next=' + window.location.pathname;
        return;
    }
    
    const container = form.closest('.comments-section');
    if (!container) return;
    
    const postId = container.querySelector('.reaction-buttons')?.dataset.postId;
    
    const textarea = form.querySelector('textarea');
    const content = textarea.value.trim();
    
    if (!content) {
        this.authService.showMessage('Введите текст комментария', 'error');
        textarea.focus();
        return;
    }
    
    if (content.length > 1000) {
        this.authService.showMessage('Комментарий слишком длинный (макс. 1000 символов)', 'error');
        return;
    }

    const submitBtn = form.querySelector('button[type="submit"]');
    const originalText = submitBtn.innerHTML;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Отправка...';
    submitBtn.disabled = true;
    
    try {
        const response = await this.authService.authFetch(`/posts/${postId}/comment/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ content: content })
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            textarea.value = '';
            this.addNewComment(data.comment_html);
            this.updateCommentCount(data.comments_count);
            this.authService.showMessage('Комментарий добавлен!', 'success');
        } else {
            this.authService.showMessage(data.error || 'Ошибка при добавлении комментария', 'error');
        }
    } catch (error) {
        console.error('Comment error:', error);
        this.authService.showMessage('Ошибка сети или сервера', 'error');
    } finally {
        submitBtn.innerHTML = originalText;
        submitBtn.disabled = false;
    }
}
    

    addNewComment(commentHtml) {
        const commentsList = document.getElementById('comments-list');
        if (!commentsList) return;

        const noComments = commentsList.querySelector('.no-comments');
        if (noComments) {
            noComments.remove();
        }

        commentsList.insertAdjacentHTML('afterbegin', commentHtml);

        const newComment = commentsList.firstElementChild;
        if (newComment) {
            newComment.style.animation = 'fadeIn 0.5s ease';
        }
    }
    
    updateCommentCount(count) {

        const commentTitle = document.querySelector('.comments-section h3');
        if (commentTitle) {
            commentTitle.textContent = `Комментарии (${count})`;
        }

        document.querySelectorAll('.comment-count').forEach(el => {
            el.textContent = count;
        });
    }
    
    initCreatePostForm() {
        const form = document.getElementById('create-post-form');
        if (!form) return;
        
        if (!this.authService.isAuthenticated()) {
            this.showLoginRequired('create-post');
            return;
        }
        
        form.addEventListener('submit', (e) => this.handleCreatePost(e));
    }
    
    async handleCreatePost(event) {
        event.preventDefault();
        
        const form = event.currentTarget;
        const formData = new FormData(form);
        const submitBtn = form.querySelector('button[type="submit"]');
        const originalText = submitBtn.textContent;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Публикация...';
        submitBtn.disabled = true;
        
        try {
            const response = await this.authService.authFormDataFetch('/posts/api/create/', formData);
            
            const data = await response.json();
            
            if (response.ok && data.success) {
                window.location.href = data.redirect_url;
            } else {
                this.showFormErrors(form, data.errors || {});
                this.authService.showMessage('Ошибка при создании новости', 'error');
            }
        } catch (error) {
            console.error('Create post error:', error);
            this.authService.showMessage('Ошибка сети', 'error');
        } finally {
            submitBtn.textContent = originalText;
            submitBtn.disabled = false;
        }
    }
    
    showLoginRequired(elementId) {
        const element = document.getElementById(elementId);
        if (!element) return;
        
        element.innerHTML = `
            <div style="text-align: center; padding: 40px;">
                <div style="font-size: 4rem; color: rgba(255,255,255,0.1); margin-bottom: 20px;">
                    <i class="fas fa-lock"></i>
                </div>
                <h2>Требуется авторизация</h2>
                <p style="color: #888; margin: 20px 0;">
                    Для выполнения этого действия необходимо войти в систему
                </p>
                <div style="display: flex; gap: 15px; justify-content: center; margin-top: 30px;">
                    <a href="/login/" class="btn btn-accent">Войти</a>
                    <a href="/register/" class="btn btn-outline">Зарегистрироваться</a>
                </div>
            </div>
        `;
    }
    
    showFormErrors(form, errors) {
        form.querySelectorAll('.form-error').forEach(el => el.remove());
        
        for (const field in errors) {
            const input = form.querySelector(`[name="${field}"]`);
            if (input) {
                const errorDiv = document.createElement('div');
                errorDiv.className = 'form-error';
                errorDiv.style.cssText = `
                    color: #f44336;
                    font-size: 14px;
                    margin-top: 5px;
                    padding: 5px;
                    background: rgba(244, 67, 54, 0.1);
                    border-radius: 4px;
                `;
                errorDiv.textContent = errors[field].join(', ');
                input.parentNode.appendChild(errorDiv);
            }
        }
    }
    
    initAll() {
        this.initReactionButtons();
        this.initCommentForm();
        this.initCreatePostForm();
        this.addAnimations();
    }

    addAnimations() {
        if (!document.querySelector('#post-animations')) {
            const style = document.createElement('style');
            style.id = 'post-animations';
            style.textContent = `
                @keyframes fadeIn {
                    from { opacity: 0; transform: translateY(-10px); }
                    to { opacity: 1; transform: translateY(0); }
                }
                
                .reaction-btn.active {
                    animation: pulse 0.3s ease;
                }
                
                @keyframes pulse {
                    0% { transform: scale(1); }
                    50% { transform: scale(1.1); }
                    100% { transform: scale(1); }
                }
            `;
            document.head.appendChild(style);
        }
    }
}

window.postService = new PostService();

document.addEventListener('DOMContentLoaded', function() {
    window.postService.initAll();
});