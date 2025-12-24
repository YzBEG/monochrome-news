from django.http import HttpResponseForbidden
from django.utils.deprecation import MiddlewareMixin

class AdminAccessMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if request.path.startswith('/admin/'):
            if hasattr(request, 'user') and request.user.is_authenticated:
                if not request.user.is_staff:
                    return HttpResponseForbidden(
                        '<h1>Доступ запрещен</h1>'
                        '<p>У вас нет прав для доступа к панели администратора.</p>'
                    )
            else:
                from django.shortcuts import redirect
                return redirect(f'/login/?next={request.path}')
        return None