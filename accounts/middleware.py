from django.shortcuts import redirect
from django.contrib import messages

class EmailConfirmationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Пути, где проверка email не нужна
        exempt_paths = [
            '/accounts/login/',
            '/accounts/logout/',
            '/accounts/register/',
            '/accounts/resend-confirmation/',
            '/admin/',
            '/',  # главная страница
        ]
        
        # Добавляем все пути для подтверждения email (с любыми параметрами)
        if request.path.startswith('/accounts/confirm-email/'):
            exempt_paths.append(request.path)
        
        if (request.user.is_authenticated and 
            not request.user.email_confirmed and
            request.path not in exempt_paths):
            
            messages.warning(
                request,
                'Ваш email не подтверждён. '
                'Пожалуйста, подтвердите email для полного доступа к функциям сайта.'
            )
        
        response = self.get_response(request)
        return response