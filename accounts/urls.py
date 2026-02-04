from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [

    # 注册 API：POST /api/auth/register/    
    path('register/',views.RegisterView.as_view(),name='register'),

    # 登录 API：POST /api/auth/login/
    path('login/',views.LoginView.as_view(),name='login'),

    # 获取用户信息 API：GET /api/auth/profile/
    path('profile/',views.ProfileView.as_view(),name='profile'),
]