class FormService {
    constructor() {
        this.authService = window.authService;
    }
    
    showMessage(text, type = 'info') {
        if (window.showMonochromeMessage) {
            window.showMonochromeMessage(text, type);
        } else if (this.authService && this.authService.showMessage) {
            this.authService.showMessage(text, type);
        }
    }

    initLoginForm() {
        const form = document.getElementById('login-form');
        if (!form) return;
        if (this.authService.isAuthenticated()) {
            window.location.href = '/';
            return;
        }
        
        form.addEventListener('submit', (e) => this.handleLogin(e));
    }
    
    async handleLogin(event) {
        event.preventDefault();
        
        const form = event.currentTarget;
        const username = form.querySelector('#username').value.trim();
        const password = form.querySelector('#password').value;
        
        if (!username || !password) {
            this.showError(form, 'Заполните все поля');
            return;
        }
        
        const submitBtn = form.querySelector('button[type="submit"]');
        const originalText = submitBtn.textContent;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Вход...';
        submitBtn.disabled = true;
        
        try {
            const response = await fetch('/api/login/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken()
                },
                body: JSON.stringify({ 
                    username: username, 
                    password: password 
                })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                this.authService.setAuthData(data);
                
                const urlParams = new URLSearchParams(window.location.search);
                const nextUrl = urlParams.get('next') || '/';
                window.location.href = nextUrl;
            } else {
                this.showError(form, data.error || 'Ошибка при входе');
            }
        } finally {
            submitBtn.textContent = originalText;
            submitBtn.disabled = false;
        }
    }
    
    initRegisterForm() {
        const form = document.getElementById('register-form');
        if (!form) return;
        
        if (this.authService.isAuthenticated()) {
            window.location.href = '/';
            return;
        }
        
        form.addEventListener('submit', (e) => this.handleRegister(e));
        
        const passwordInput = form.querySelector('#password');
        const passwordConfirmInput = form.querySelector('#password2');
        
        if (passwordInput && passwordConfirmInput) {
            passwordConfirmInput.addEventListener('input', () => {
                this.validatePasswordMatch(passwordInput, passwordConfirmInput);
            });
        }
    }
    
    async handleRegister(event) {
        event.preventDefault();
        
        const form = event.currentTarget;
        const username = form.querySelector('#username').value.trim();
        const email = form.querySelector('#email').value.trim();
        const password = form.querySelector('#password').value;
        const password2 = form.querySelector('#password2').value;
        
        if (!username || !email || !password || !password2) {
            this.showError(form, 'Заполните все поля');
            return;
        }
        
        if (password !== password2) {
            this.showError(form, 'Пароли не совпадают');
            return;
        }
        
        if (password.length < 6) {
            this.showError(form, 'Пароль должен быть не менее 6 символов');
            return;
        }
        
        const submitBtn = form.querySelector('button[type="submit"]');
        const originalText = submitBtn.textContent;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Регистрация...';
        submitBtn.disabled = true;
        
        try {
            const response = await fetch('/api/register/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken()
                },
                body: JSON.stringify({ 
                    username: username, 
                    email: email, 
                    password: password, 
                    password2: password2 
                })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                this.authService.setAuthData(data);
                window.location.href = '/';
            } else {
                this.showError(form, data.error || 'Ошибка при регистрации');
            }
        } finally {
            submitBtn.textContent = originalText;
            submitBtn.disabled = false;
        }
    }

    validatePasswordMatch(passwordInput, confirmInput) {
        const password = passwordInput.value;
        const confirm = confirmInput.value;
        
        if (password && confirm && password !== confirm) {
            this.showFieldError(confirmInput, 'Пароли не совпадают');
        } else {
            this.clearFieldError(confirmInput);
        }
    }
    

    showError(form, message) {
        this.clearFormErrors(form);
        const errorDiv = document.createElement('div');
        errorDiv.className = 'form-error-message';
        errorDiv.style.cssText = `
            background: rgba(244, 67, 54, 0.1);
            color: #f44336;
            padding: 12px;
            border-radius: 6px;
            margin-bottom: 20px;
            border-left: 4px solid #f44336;
            animation: fadeIn 0.3s ease;
        `;
        errorDiv.textContent = message;

        const errorContainer = form.querySelector('#form-error') || form;
        errorContainer.insertBefore(errorDiv, errorContainer.firstChild);
    }
    

    showFieldError(input, message) {
        this.clearFieldError(input);
        const errorDiv = document.createElement('div');
        errorDiv.className = 'field-error';
        errorDiv.style.cssText = `
            color: #f44336;
            font-size: 14px;
            margin-top: 5px;
            padding: 5px;
        `;
        errorDiv.textContent = message;
    
        input.parentNode.appendChild(errorDiv);
        
        input.classList.add('error');
    }
    

    clearFormErrors(form) {
        form.querySelectorAll('.form-error-message').forEach(el => el.remove());
    }
    
    clearFieldError(input) {
        const errorDiv = input.parentNode.querySelector('.field-error');
        if (errorDiv) {
            errorDiv.remove();
        }
        input.classList.remove('error');
    }
    
    getCsrfToken() {
        const csrfInput = document.querySelector('[name=csrfmiddlewaretoken]');
        return csrfInput ? csrfInput.value : null;
    }

    initAll() {
        this.initLoginForm();
        this.initRegisterForm();
        this.addFormStyles();
    }
    
    addFormStyles() {
        if (!document.querySelector('#form-styles')) {
            const style = document.createElement('style');
            style.id = 'form-styles';
            style.textContent = `
                @keyframes fadeIn {
                    from { opacity: 0; }
                    to { opacity: 1; }
                }
                
                .form-control.error {
                    border-color: #f44336 !important;
                    background: rgba(244, 67, 54, 0.05) !important;
                }
                
                .field-error {
                    animation: fadeIn 0.3s ease;
                }
                
                .form-error-message {
                    animation: fadeIn 0.3s ease;
                }
            `;
            document.head.appendChild(style);
        }
    }
}

window.formService = new FormService();

document.addEventListener('DOMContentLoaded', function() {
    window.formService.initAll();
});