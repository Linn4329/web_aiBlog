import json
import time
from django.http import StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from .services import AIService
from .models import ChatSession, ChatMessage, AIUsageLog
from rest_framework.response import Response
from rest_framework import status


@api_view(['post'])
@permission_classes([IsAuthenticated])
def generate_summary(request):
    """
    文章摘要接口 POST /api/ai/summarize/
    
    优化点：
    1. 超时控制（30秒）
    2. 异常分类处理
    3. 自动重试机制（最多3次）
    4. 友好的错误提示
    
    请求体：
    {
        "content": "文章正文...",  // 必填
        "max_length": 200          // 可选，默认200字
    }
    
    响应：
    {
        "summary": "生成的摘要..."
    }
    """
    # 1. 获取并校验参数
    content = request.data.get('content', '').strip()
    max_length = request.data.get('max_length', 200)

    if not content:
        return Response(
            {'error': '文章内容不能为空'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # 2. 初始化AI服务（设置30秒超时）
    ai = AIService(timeout=30)
    
    # 3. 带重试的摘要生成
    summary = None
    last_error = None
    max_retries = 3
    
    for attempt in range(max_retries):
        try:
            # 尝试生成摘要
            summary = ai.generate_summary(content, max_length)
            break  # 成功，跳出循环
            
        except TimeoutError as e:
            # 超时错误，记录并准备重试
            last_error = str(e)
            if attempt < max_retries - 1:
                time.sleep(1)  # 等待1秒后重试
                continue
            break  # 最后一次也超时，跳出
            
        except Exception as e:
            # 其他错误（API错误、网络错误等）
            last_error = str(e)
            if attempt < max_retries - 1:
                time.sleep(1)
                continue
            break
    
    # 4. 处理失败情况
    if summary is None:
        # 记录失败日志
        AIUsageLog.objects.create(
            user=request.user,
            call_type='summarize',
            prompt_summary=content[:50] + "...",
            success=False,
            error_message=last_error,
        )
        return Response(
            {
                'error': '生成摘要失败',
                'detail': last_error,
                'suggestion': '请稍后重试，或缩短文章内容'
            },
            status=status.HTTP_503_SERVICE_UNAVAILABLE  # 503: 服务暂时不可用
        )
    
    # 5. 记录成功日志
    AIUsageLog.objects.create(
        user=request.user,
        call_type='summarize',
        prompt_summary=content[:50] + "...",
        success=True,
    )

    # 6. 返回成功响应
    return Response({"summary": summary})


@api_view(['post'])
@permission_classes([IsAuthenticated])
def chat_stream(request):
    """
    AI流式对话接口 POST /api/ai/chat/
    
    优化点：
    1. 超时控制（60秒）
    2. 流式异常处理（通过SSE发送错误）
    3. 错误时不保存不完整回复
    4. 前端可识别错误类型
    
    请求体：
    {
        "session_id": 1,        // 可选，不传则创建新会话
        "message": "你好"        // 用户消息
    }
    
    返回: SSE流 text/event-stream
    错误格式: data: {"type": "error", "message": "..."}
    """
    user = request.user
    session_id = request.data.get('session_id')
    message = request.data.get('message', '').strip()
    
    # 1. 参数校验
    if not message:
        return StreamingHttpResponse(
            "data: " + json.dumps({"type": "error", "message": "消息不能为空"}) + "\n\n",
            content_type="text/event-stream",
        )
    
    # 2. 获取或创建会话
    if session_id:
        session = ChatSession.objects.filter(id=session_id, user=user).first()
        if not session:
            return StreamingHttpResponse(
                "data: " + json.dumps({"type": "error", "message": "会话不存在或无权限"}) + "\n\n",
                content_type="text/event-stream",
            )
    else:
        session = ChatSession.objects.create(
            user=user,
            title=message[:20]
        )

    # 3. 保存用户消息
    ChatMessage.objects.create(
        content=message,
        role='user',
        session=session,
    )

    # 4. 构建历史消息（取最近20条）
    history = ChatMessage.objects.filter(session=session).order_by('-id')[:20]
    messages = [{"role": msg.role, "content": msg.content} for msg in reversed(history)]

    # 5. 初始化AI服务（流式请求需要更长超时）
    ai = AIService(timeout=60)
    
    def event_stream():
        """
        SSE事件生成器
        通过yield实时发送数据给前端
        """
        full_response = []
        error_occurred = False
        error_message = ""
        
        # 5.1 发送会话ID（前端需要保存）
        yield f"data: {json.dumps({'type': 'session', 'session_id': session.id})}\n\n"
        
        try:
            # 5.2 流式获取AI回复
            for chunk in ai.chat_stream(messages):
                full_response.append(chunk)
                # 实时发送给前端
                yield f"data: {json.dumps({'type': 'content', 'text': chunk})}\n\n"
                
        except TimeoutError as e:
            # 超时错误
            error_occurred = True
            error_message = str(e)
            yield f"data: {json.dumps({'type': 'error', 'error_type': 'timeout', 'message': error_message})}\n\n"
            
        except Exception as e:
            # 其他错误（API错误、网络错误等）
            error_occurred = True
            error_message = str(e)
            yield f"data: {json.dumps({'type': 'error', 'error_type': 'api_error', 'message': error_message})}\n\n"
        
        # 5.3 保存完整回复（只有成功时才保存）
        if not error_occurred and full_response:
            complete_text = ''.join(full_response)
            ChatMessage.objects.create(
                session=session,
                role='assistant',
                content=complete_text
            )
            # 记录成功日志
            AIUsageLog.objects.create(
                user=user,
                call_type='chat',
                prompt_summary=message[:50] + "...",
                success=True,
            )
        else:
            # 记录失败日志
            AIUsageLog.objects.create(
                user=user,
                call_type='chat',
                prompt_summary=message[:50] + "...",
                success=False,
                error_message=error_message,
            )
        
        # 5.4 发送结束标记
        yield f"data: {json.dumps({'type': 'done', 'has_error': error_occurred})}\n\n"
    
    # 6. 返回SSE响应
    response = StreamingHttpResponse(
        event_stream(),
        content_type='text/event-stream'
    )
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'  # 禁用Nginx缓冲
    return response
