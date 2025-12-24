document.addEventListener('DOMContentLoaded', function() {
    console.log('MONOCHROME NEWS initialized');
    
    if (window.authService) {
        window.authService.updateUI();
    }
    
    if (window.postService) {
        window.postService.initAll();
    }
    
    if (window.formService) {
        window.formService.initAll();
    }
    
    checkProtectedPages();
    
    initTooltips();
    
    initProfileLinks();
});


function checkProtectedPages() {
    const protectedPages = [
        '/posts/create/',
        '/users/edit-profile/'
    ];
    
    const currentPath = window.location.pathname;
    
    if (protectedPages.some(page => currentPath.startsWith(page))) {
        if (!window.authService || !window.authService.isAuthenticated()) {
            window.location.href = `/login/?next=${currentPath}`;
        }
    }
}


function initTooltips() {
    document.querySelectorAll('[data-tooltip]').forEach(element => {
        element.addEventListener('mouseenter', showTooltip);
        element.addEventListener('mouseleave', hideTooltip);
    });
}

function showTooltip(event) {
    const element = event.currentTarget;
    const tooltipText = element.getAttribute('data-tooltip');
    
    const tooltip = document.createElement('div');
    tooltip.className = 'custom-tooltip';
    tooltip.textContent = tooltipText;
    tooltip.style.cssText = `
        position: absolute;
        background: rgba(0, 0, 0, 0.9);
        color: white;
        padding: 8px 12px;
        border-radius: 4px;
        font-size: 14px;
        z-index: 10000;
        white-space: nowrap;
        pointer-events: none;
        animation: fadeIn 0.2s ease;
    `;
    
    const rect = element.getBoundingClientRect();
    tooltip.style.top = `${rect.top - 40}px`;
    tooltip.style.left = `${rect.left + rect.width / 2}px`;
    tooltip.style.transform = 'translateX(-50%)';
    
    tooltip.innerHTML += `
        <div style="
            position: absolute;
            top: 100%;
            left: 50%;
            transform: translateX(-50%);
            border: 6px solid transparent;
            border-top-color: rgba(0, 0, 0, 0.9);
        "></div>
    `;
    
    document.body.appendChild(tooltip);
    element._tooltip = tooltip;
}

function hideTooltip(event) {
    const element = event.currentTarget;
    if (element._tooltip) {
        element._tooltip.remove();
        delete element._tooltip;
    }
}

function initProfileLinks() {
    document.querySelectorAll('a[href^="/users/"]').forEach(link => {
        const href = link.getAttribute('href');
        if (href.includes('/users/') && !href.includes('/login') && !href.includes('/register')) {
            link.addEventListener('click', function(e) {
                console.log('Переход на профиль:', href);
            });
        }
    });
    
    document.querySelectorAll('.user-link').forEach(link => {
        const username = link.textContent.trim();
        link.setAttribute('data-tooltip', `Профиль ${username}`);
        link.addEventListener('mouseenter', showTooltip);
        link.addEventListener('mouseleave', hideTooltip);
    });
}

function showMessage(message, type = 'info', duration = 3000) {
    if (window.showMonochromeMessage) {
        window.showMonochromeMessage(message, type, duration);
    } else if (window.authService) {
        window.authService.showMessage(message, type, duration);
    } else {
        console.log(`${type.toUpperCase()}: ${message}`);
    }
}

function checkConnection() {
    if (!navigator.onLine) {
        showMessage('Отсутствует интернет соединение', 'error', 5000);
    }
}

window.addEventListener('online', () => {
    showMessage('Соединение восстановлено', 'success', 3000);
});

window.addEventListener('offline', () => {
    showMessage('Отсутствует интернет соединение', 'error', 5000);
});

checkConnection();

function checkDjangoMessages() {
    const messagesContainer = document.querySelector('.messages');
    if (messagesContainer) {
        const messages = messagesContainer.querySelectorAll('.message');
        messages.forEach(msg => {
            const text = msg.textContent.trim();
            const isSuccess = msg.classList.contains('success');
            const isError = msg.classList.contains('error');
            
            if (isSuccess) {
                showMessage(text, 'success', 4000);
            } else if (isError) {
                showMessage(text, 'error', 4000);
            }
            
            setTimeout(() => msg.remove(), 4000);
        });
    }
}

document.addEventListener('DOMContentLoaded', function() {
    checkDjangoMessages();
});