from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import Profile
from .serializers import ProfileSerializer, ProfileUpdateSerializer

# Create your views here.

class ProfileDetailView(APIView):
    """个人资料视图 - 获取和更新个人资料"""
    permission_classes = [IsAuthenticated]  # 需要登录

    def get(self, request):
        """获取个人资料"""
        # 确保用户有 Profile 对象
        profile,created = Profile.objects.get_or_create(user=request.user)
        serializer = ProfileSerializer(profile)
        return Response({
            'message': '获取个人资料成功',
            'profile':serializer.data
        },status=status.HTTP_200_OK)

    def post(self, request):
        """更新个人资料"""
        # 确保用户有 Profile 对象
        profile,created = Profile.objects.get_or_create(user=request.user)
        
        # 使用 partial=True 允许部分更新
        serilizer = ProfileUpdateSerializer(
            profile,
            data = request.data,
            parital = True
        )

        if not serilizer.is_valid():
            return Response({
                'error':'更新失败',
                'message':serilizer.errors
            },status=status.HTTP_400_BAD_REQUEST)
        serilizer.save()


        # 返回更新后的完整数据
        profile_serializer = ProfileSerializer(profile)
        return Response({
            'message': '更新成功',
            'profile': profile_serializer.data
        }, status=status.HTTP_200_OK)



