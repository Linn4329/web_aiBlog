from rest_framework import serializers
from .models import Tag,Post

class TagSerializer(serializers.ModelSerializer):
    """标签展示序列化器（只读）"""
    
    class Meta:
        model = Tag
        fields = ['id', 'name', 'slug', 'created_at']
        read_only_fields = ['id', 'created_at']


class TagCreateSerializer(serializers.ModelSerializer):
    """标签创建序列化器"""

    name = serializers.CharField(
        error_messages={'unique': '该标签已存在'}
    )
    
    class Meta:
        model = Tag
        fields = ['name']
        
    def validate_name(self, value):
        """验证标签名称唯一性"""
        if Tag.objects.filter(name=value).exists():
            raise serializers.ValidationError("该标签已存在")
        return value


class PostSerializer(serializers.ModelSerializer):
    """文章展示序列化器（只读）"""
    author = serializers.SerializerMethodField()  # 自定义字段，获取用户名
    
    class Meta:
        model = Post
        fields = [
            'id', 'title', 'author', 'excerpt', 
            'cover_image', 'status', 'view_count', 
            'tags', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'view_count']
        
    def get_author(self, obj):
        """获取作者的用户名"""
        return obj.author.username if obj.author else None


class PostCreateUpdateSerializer(serializers.ModelSerializer):
    """文章创建/更新序列化器"""
    
    # 添加错误消息配置
    title = serializers.CharField(
        error_messages={'required': '标题不能为空', 'blank': '标题不能为空'}
    )
    excerpt = serializers.CharField(
        error_messages={'required': '摘要不能为空', 'blank': '摘要至少需要 10 个字符'}
    )


    class Meta:
        model = Post
        fields = ['title', 'content', 'excerpt', 'cover_image', 'status', 'tags']
        
    def validate_title(self, value):
        """验证标题不为空"""
        if not value or not value.strip():
            raise serializers.ValidationError("标题不能为空")
        return value
        
    def validate_excerpt(self, value):
        """验证摘要不为空且不为纯空格"""
        if not value or not value.strip():
            raise serializers.ValidationError("摘要不能为空")
        if len(value) < 10:
            raise serializers.ValidationError("摘要至少需要 10 个字符")
        return value
        
    def validate_status(self, value):
        """验证状态值的有效性"""
        valid_statuses = [choice[0] for choice in Post.STATUS_CHOICES]
        if value not in valid_statuses:
            raise serializers.ValidationError(f"状态必须是以下之一：{', '.join(valid_statuses)}")
        return value
        
    def create(self, validated_data):
        """创建文章时自动设置作者"""
        tags_data = validated_data.pop('tags', [])
        post = Post.objects.create(**validated_data)
        if tags_data:
            post.tags.set(tags_data)
        return post
        
    def update(self, instance, validated_data):
        """更新文章"""
        tags_data = validated_data.pop('tags', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if tags_data is not None:
            instance.tags.set(tags_data)
        return instance
