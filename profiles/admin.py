from django.contrib import admin
from .models import Profile
# Register your models here.

# @admin.register(Profile)：装饰器，将 Profile 模型注册到后台
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    """个人资料后台管理"""
    # 获得后台管理的默认功能，并自定义行为

    # 列表页显示哪些字段
    list_display = ['user','nickname','location','gender','created_at']

    # 右侧添加过滤器
    list_filter = ['gender','created_at','updated_at']

    # 添加搜索框，支持模糊搜索
    search_fields = ['user_name','nickname','bio','location']

    # 只读字段，禁止手动修改
    readonly_fields = ['created_at','updated_at']

    # 将字段分组显示，界面更清晰
    fieldsets = (
        ('基本信息', {
            'fields': ('user', 'nickname', 'gender')
        }),
        ('详细信息', {
            'fields': ('avatar', 'bio', 'website', 'location', 'birth_date')
        }),
        ('时间信息', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)  # 默认折叠
        }),
    )