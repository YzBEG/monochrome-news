class AuthService {
    constructor() {
        this.accessToken = localStorage.getItem('access_token');
        this.refreshToken = localStorage.getItem('refresh_token');
        this.user = JSON.parse(localStorage.getItem('user') || 'null');
        
        
        if (this.isAuthenticated()) {
            this.startHeartbeat();
        }
    }
    async authFormDataFetch(url, formData, options = {}) {
        options.headers = options.headers || {};
        
       
        if (this.accessToken) {
            options.headers['Authorization'] = `Bearer ${this.accessToken}`;
        }
        
        
        const csrfToken = this.getCsrfToken();
        if (csrfToken) {
            options.headers['X-CSRFToken'] = csrfToken;
        }
        
        options.body = formData;
        
        let response = await fetch(url, options);
        
        
        if (response.status === 401) {
            try {
                const newToken = await this.refreshAccessToken();
                if (newToken) {
                    options.headers['Authorization'] = `Bearer ${newToken}`;
                    response = await fetch(url, options);
                } else {
                    this.clearAuthData();
                    window.location.href = '/login/';
                    throw new Error('Token refresh failed');
                }
            } catch (refreshError) {
                console.error('Token refresh failed:', refreshError);
                this.clearAuthData();
                window.location.href = '/login/';
                throw refreshError;
            }
        }
        
        return response;
    }
    
    
    
    isAuthenticated() {
        
        if (!this.accessToken || !this.user) {
            return false;
        }
        
        return true;
    }
    
    
    getCurrentUser() {
        return this.user;
    }
    
    
    getUsername() {
        return this.user ? this.user.username : null;
    }
    
    
    getUserId() {
        return this.user ? this.user.id : null;
    }
    
    
    setAuthData(data) {
        if (!data.tokens || !data.tokens.access || !data.tokens.refresh) {
            console.error('Invalid auth data:', data);
            return false;
        }
        
        this.accessToken = data.tokens.access;
        this.refreshToken = data.tokens.refresh;
        this.user = data.user || data;
        
        localStorage.setItem('access_token', data.tokens.access);
        localStorage.setItem('refresh_token', data.tokens.refresh);
        localStorage.setItem('user', JSON.stringify(data.user || data));
        
        
        this.setCookie('access_token', data.tokens.access, 1); 
        this.setCookie('refresh_token', data.tokens.refresh, 7); 
        
        
        this.startHeartbeat();
        
        
        this.updateUI();
        
        return true;
    }
    
    
    clearAuthData() {
        this.accessToken = null;
        this.refreshToken = null;
        this.user = null;      
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user');
        this.deleteCookie('access_token');
        this.deleteCookie('refresh_token');
        this.stopHeartbeat();
        this.updateUI();
    }
    
 
    async authFetch(url, options = {}) {
        options.headers = options.headers || {};

        if (this.accessToken) {
            options.headers['Authorization'] = `Bearer ${this.accessToken}`;
        }

        const csrfToken = this.getCsrfToken();
        if (csrfToken) {
            options.headers['X-CSRFToken'] = csrfToken;
        }
        
        let response = await fetch(url, options);

        if (response.status === 401) {
            try {
                const newToken = await this.refreshAccessToken();
                if (newToken) {
                    options.headers['Authorization'] = `Bearer ${newToken}`;
                    response = await fetch(url, options);
                } else {
                    this.clearAuthData();
                    window.location.href = '/login/';
                    throw new Error('Token refresh failed');
                }
            } catch (refreshError) {
                console.error('Token refresh failed:', refreshError);
                this.clearAuthData();
                window.location.href = '/login/';
                throw refreshError;
            }
        }
        
        return response;
    }
    

    async refreshAccessToken() {
        if (!this.refreshToken) {
            console.error('No refresh token available');
            return null;
        }
        
        try {
            const response = await fetch('/api/token/refresh/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ refresh: this.refreshToken })
            });
            
            if (response.ok) {
                const data = await response.json();
                this.accessToken = data.access;
                localStorage.setItem('access_token', data.access);
                this.setCookie('access_token', data.access, 1);
                console.log('Token refreshed successfully');
                return data.access;
            } else {
                console.error('Refresh token invalid');
                this.clearAuthData();
                window.location.href = '/login/';
                return null;
            }
        } catch (error) {
            console.error('Token refresh error:', error);
            this.clearAuthData();
            window.location.href = '/login/';
            return null;
        }
    }
    

    async logout() {
        if (this.refreshToken) {
            try {
                await fetch('/api/logout/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${this.accessToken}`
                    },
                    body: JSON.stringify({ refresh: this.refreshToken })
                });
            } catch (error) {
                console.error('Logout API error:', error);
            }
        }
        
        this.clearAuthData();
        window.location.href = '/';
    }
    
    async sendHeartbeat() {
        if (!this.isAuthenticated()) return;
        
        try {
            await this.authFetch('/api/heartbeat/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ timestamp: Date.now() })
            });
        } catch (error) {
            console.log('Heartbeat error (normal if offline):', error.message);
        }
    }
    

    startHeartbeat() {
        this.sendHeartbeat();
        this.heartbeatInterval = setInterval(() => {
            this.sendHeartbeat();
        }, 30000);
    }
    
    stopHeartbeat() {
        if (this.heartbeatInterval) {
            clearInterval(this.heartbeatInterval);
            this.heartbeatInterval = null;
        }
    }
    

    updateUI() {
        this.updateNavigation();
        this.updateAuthElements();
    }
    
    updateNavigation() {
        const authButtons = document.querySelector('.auth-buttons');
        if (!authButtons) return;
        
        if (this.isAuthenticated()) {
            authButtons.innerHTML = `
                <div style="display: flex; align-items: center; gap: 15px;">
                    <span class="user-greeting">
                        <i class="fas fa-user"></i> ${this.user.username}
                    </span>
                    <button onclick="authService.logout()" class="btn btn-outline" style="padding: 8px 16px;">
                        <i class="fas fa-sign-out-alt"></i> Выйти
                    </button>
                </div>
            `;
        } else {
            authButtons.innerHTML = `
                <a href="/login/" class="btn btn-outline">Войти</a>
                <a href="/register/" class="btn btn-accent">Регистрация</a>
            `;
        }
    }
    

    updateAuthElements() {
        document.querySelectorAll('[data-auth="required"]').forEach(el => {
            el.style.display = this.isAuthenticated() ? '' : 'none';
        });
        
        document.querySelectorAll('[data-auth="guest"]').forEach(el => {
            el.style.display = this.isAuthenticated() ? 'none' : '';
        });
        
        document.querySelectorAll('[data-auth-username]').forEach(el => {
            if (this.user) {
                el.textContent = this.user.username;
            }
        });
    }
    

    getCsrfToken() {
        const csrfInput = document.querySelector('[name=csrfmiddlewaretoken]');
        return csrfInput ? csrfInput.value : null;
    }

    setCookie(name, value, days) {
        const expires = new Date();
        expires.setTime(expires.getTime() + (days * 24 * 60 * 60 * 1000));
        document.cookie = `${name}=${value};expires=${expires.toUTCString()};path=/;SameSite=Lax`;
    }
    
    deleteCookie(name) {
        document.cookie = `${name}=;expires=Thu, 01 Jan 1970 00:00:00 GMT;path=/`;
    }
    

    showMessage(text, type = 'info', duration = 3000) {
        let container = document.getElementById('message-container');
            if (window.showMonochromeMessage) {
            window.showMonochromeMessage(text, type, duration);
            return;
        }

    
        const message = document.createElement('div');
        message.className = `auth-message auth-message-${type}`;
        message.style.cssText = `
            padding: 12px 20px;
            background: ${this.getMessageColor(type)};
            color: white;
            border-radius: 0;
            border: 1px solid rgba(255,255,255,0.2);
            border-left: 3px solid ${this.getMessageBorderColor(type)};
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            animation: slideIn 0.3s ease;
            max-width: 300px;
            word-wrap: break-word;
            font-family: 'Segoe UI', sans-serif;
            font-size: 13px;
            letter-spacing: 1px;
            text-transform: uppercase;
            backdrop-filter: blur(10px);
        `;
        message.textContent = text;
        
        container.appendChild(message);
        

        setTimeout(() => {
            message.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => message.remove(), 300);
        }, duration);
    }
    

    getMessageColor(type) {
        const colors = {
            'success': 'rgba(126, 126, 126, 0.95)',
            'error': 'rgba(126, 126, 126, 0.95)',
            'warning': 'rgba(126, 126, 126, 0.95)',
            'info': 'rgba(126, 126, 126, 0.95)'
        };
        return colors[type] || colors.info;
    }
    
    getMessageBorderColor(type) {
        const colors = {
            'success': '#000',
            'error': '#000000ff',
            'warning': '#000000ff',
            'info': '#000000ff'
        };
        return colors[type] || colors.info;
    }
}

window.authService = new AuthService();

document.addEventListener('DOMContentLoaded', function() {
    window.authService.updateUI();
    
    if (!document.querySelector('#auth-message-styles')) {
        const style = document.createElement('style');
        style.id = 'auth-message-styles';
        style.textContent = `
            @keyframes slideIn {
                from { transform: translateX(100%); opacity: 0; }
                to { transform: translateX(0); opacity: 1; }
            }
            @keyframes slideOut {
                from { transform: translateX(0); opacity: 1; }
                to { transform: translateX(100%); opacity: 0; }
            }
        `;
        document.head.appendChild(style);
    }
});