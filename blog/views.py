from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework.exceptions import PermissionDenied
from django.http import Http404
from django.db.models import F
from .models import Tag, Post
from .serializers import (
    TagSerializer, 
    TagCreateSerializer, 
    PostSerializer, 
    PostCreateUpdateSerializer
)

# PageNumberPagination：DRF 内置分页器，基于页码（page=1, page=2）
class PostPagination(PageNumberPagination):
    """文章列表分页器"""
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class TagListAPIView(APIView):
    """标签列表视图 - 获取所有标签 / 创建新标签"""

    permission_classes = []  # 覆盖全局权限，手动处理认证
    def get(self,request):
        """
        GET /api/blog/tags/
        获取所有标签列表（公开访问）
        """
        try:
            tags = Tag.objects.all().order_by('-created_at')
            # many=True：序列化多个对象（QuerySet）
            serializer = TagSerializer(tags, many=True)
            return Response({
                'message': '获取标签列表成功',
                'tags':serializer.data, 
                } ,status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'message': '获取标签列表失败',
                'error': str(e)
            },status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def post(self,request):
        """
        POST /api/blog/tags/
        创建新标签（需要认证）
        """

        if not request.user.is_authenticated:
            return Response({
                'message': '请先登录'
            },status=status.HTTP_401_UNAUTHORIZED)
        
        serializer = TagCreateSerializer(data=request.data)

        if not serializer.is_valid():
            return Response({
                'message': '创建标签失败',
                'error': serializer.errors
            },status=status.HTTP_400_BAD_REQUEST)
        
        tag = serializer.save()

        return Response({
            'message': '创建标签成功',
            'tag': TagSerializer(tag).data
        },status=status.HTTP_201_CREATED)
    

class PostListView(APIView):
    """文章列表视图 - 获取文章列表 / 创建新文章"""

    permission_classes = []  # 覆盖全局权限，手动处理认证
    def get(self, request):
        """
        GET /api/blog/posts/
        分页获取已发布文章列表（公开访问）
        """

        try:
            # 只返回已发布的文章
            posts = Post.objects.filter(status='published').order_by('-created_at')

            posts = posts.select_related('author').prefetch_related("tags")

            paginator = PostPagination()
            result_page = paginator.paginate_queryset(posts, request)
            serializer = PostSerializer(result_page, many=True)

            # 构造符合测试期望的响应格式
            return Response({
                'message': '获取文章列表成功',
                'posts': serializer.data,
                'count': paginator.page.paginator.count,
                'next': paginator.get_next_link(),
                'previous': paginator.get_previous_link()
            })
        except Exception as e:
            return Response({
                'message': '获取文章列表失败',
                'error': str(e)
            },status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def post(self, request):
        """
        POST /api/blog/posts/
        创建新文章（需要认证）
        """

        if not request.user.is_authenticated:
            return Response({
                'message': '请先登录'
            },status=status.HTTP_401_UNAUTHORIZED)
        
        serializer = PostCreateUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'message':'创建文章失败',
                'error':serializer.errors
            },status=status.HTTP_400_BAD_REQUEST)
        
        # 自动设置作者为当前登录用户
        post = serializer.save(author=request.user)
        return Response({
            'message':'创建文章成功',
            'post':PostSerializer(post).data
        },status=status.HTTP_201_CREATED)
    

class PostDetailView(APIView):
    """文章详情视图 - 获取/更新/删除文章"""


    permission_classes = []  # 覆盖全局权限，手动处理认证


    def get_object(self, pk):
        try:
            return Post.objects.select_related('author').prefetch_related('tags').get(pk=pk)
        except Post.DoesNotExist:
            raise Http404('文章不存在')

    def check_object_permissions(self, request, obj):
        """检查作者权限（更新和删除时）"""
        if request.method in ['PUT', 'PATCH', 'DELETE']:
            if request.user != obj.author:
                raise PermissionDenied('无权修改他人的文章')
            
    def get(self, request, pk):
        """
        GET /api/blog/posts/{id}/
        获取文章详情（公开访问，自动增加浏览量）
        """

        try:
            post = self.get_object(pk)

            # 使用 F() 表达式更新浏览量，避免竞态条件
            # 使用 F()：在数据库层面完成增量，原子操作，避免并发请求覆盖
            Post.objects.filter(pk=pk).update(view_count=F('view_count') + 1)
            post.refresh_from_db()

            serializer = PostSerializer(post)
            return Response({
                'message': '获取文章详情成功',
                'post': serializer.data
            },status=status.HTTP_200_OK)
        
        except Http404 as e:
            return Response({
                'message': str(e)
            },status=status.HTTP_404_NOT_FOUND)
        
        except Exception as e:
            return Response({
                'message': '获取文章详情失败',
                'error': str(e)
            },status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        

    def put(self, request, pk):
        """
        PUT /api/blog/posts/{id}/
        完整更新文章（需要认证 + 作者校验）
        """
        # 前端必须传递所有字段

        if not request.user.is_authenticated:
            return Response({
                'message': '请先登录'
            },status=status.HTTP_401_UNAUTHORIZED)
        
        try:
            post = self.get_object(pk)
            self.check_object_permissions(request, post)

            serializer = PostCreateUpdateSerializer(post, data=request.data, partial=True)

            if not serializer.is_valid():
                return Response({
                    'message':' 更新失败',
                    'error':serializer.errors
                },status=status.HTTP_400_BAD_REQUEST)
            
            serializer.save()
            return Response({
                'message':'更新成功',
                'post':PostSerializer(post).data
            },status=status.HTTP_200_OK)
        
        except PermissionDenied as e:
            return Response({
                'message':str(e)
            },status=status.HTTP_403_FORBIDDEN)
        
        except Exception as e:
            return Response({
                'message':'更新失败',
                'error':str(e)
            },status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

    def patch(self, request, pk):
        """
        PATCH /api/blog/posts/{id}/
        部分更新文章（需要认证 + 作者校验）
        """
        # 前端传递修改的字段

        if not request.user.is_authenticated:
            return Response({
                'message': '请先登录'
            },status=status.HTTP_401_UNAUTHORIZED)
        try:
            post = self.get_object(pk)
            self.check_object_permissions(request, post)
            
            serializer = PostCreateUpdateSerializer(post, data=request.data, partial=True)
            if not serializer.is_valid():
                return Response({
                    'message': '更新文章失败',
                    'error': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            serializer.save()
            return Response({
                'message': '更新文章成功',
                'post': PostSerializer(post).data
            }, status=status.HTTP_200_OK)
        except PermissionDenied as e:
            return Response({
                'message': str(e)
            }, status=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            return Response({
                'message': '更新文章失败',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def delete(self, request, pk):
        """
        DELETE /api/blog/posts/{id}/
        删除文章（需要认证 + 作者校验）
        """

        if not request.user.is_authenticated:
            return Response({
                'message': '请先登录'
            },status=status.HTTP_401_UNAUTHORIZED)
        
        try:
            post = self.get_object(pk)
            self.check_object_permissions(request,post)
            post.delete()
            return Response({
                'message':'删除文章成功'
            },status=status.HTTP_200_OK)
        
        except PermissionDenied as e:
            return Response({
                'message':str(e)
            },status=status.HTTP_403_FORBIDDEN)
        
        except Exception as e:
            return Response({
                'message':'删除失败',
                'error':str(e)
            },status=status.HTTP_500_INTERNAL_SERVER_ERROR)

