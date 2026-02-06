from django.urls import path
from .views import TagListAPIView, PostListView, PostDetailView

app_name = 'blog'

urlpatterns = [
    # 标签相关路由
    path('tags/', TagListAPIView.as_view(), name='tag-list'),
    
    # 文章相关路由
    path('posts/', PostListView.as_view(), name='post-list'),
    path('posts/<int:pk>/', PostDetailView.as_view(), name='post-detail'),
]
