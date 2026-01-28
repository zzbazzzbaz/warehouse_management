from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages


# ==================== 前台视图 ====================

def login_view(request):
    """用户登录"""
    if request.user.is_authenticated:
        return redirect('frontend:product_list')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            next_url = request.GET.get('next', 'frontend:product_list')
            return redirect(next_url)
        else:
            messages.error(request, '用户名或密码错误')
    
    return render(request, 'frontend/login.html')


def logout_view(request):
    """用户登出"""
    logout(request)
    return redirect('frontend:login')
