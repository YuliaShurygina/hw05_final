from django.shortcuts import render


def page_not_found(request, exception):
    # Переменная exception содержит отладочную информацию;
    # выводить её в шаблон пользовательской страницы 404 мы не станем
    return render(request, 'core/404.html', {'path': request.path}, status=404)


def internal_server_error(request, exception):
    return render(request, 'core/500.html', {'path': request.path}, status=500)


def csrf_failure(request, reason=''):
    return render(request, 'core/403csrf.html')