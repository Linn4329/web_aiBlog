from django.contrib import admin
from .models import Tag,Post
# Register your models here.

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """标签后台管理"""
    list_display = ['name','slug','created_at']
    search_fields = ['name','slug']
    ordering = ['-created_at']
    list_per_page = 50

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    """文章后台管理"""
    list_display = ['title', 'author', 'status', 'view_count', 'created_at']
    list_filter = ['status','tags','created_at']
    search_fields = ['title','excerpt']
    raw_id_fields = ['author']
    filter_horizontal = ['tags']
    list_per_page = 20
    readonly_fields=['view_count','created_at','updated_at']
