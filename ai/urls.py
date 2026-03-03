from django.urls import path
from . import views

urlpatterns = [
    # AI对话接口
    path('chat/', views.chat_stream, name='chat'),
    path('summarize/', views.generate_summary, name='summarize'),

    # 会话管理接口
    path('sessions/', views.session_list, name='session_list'),
    path('sessions/<int:session_id>/', views.session_detail, name='session_detail'),
    path('sessions/<int:session_id>/messages/', views.session_messages, name='session_messages'),
]
