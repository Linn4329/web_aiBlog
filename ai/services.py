import os
import time
from openai import OpenAI, APITimeoutError, APIError, RateLimitError
from django.conf import settings


class AIService:
    """AI服务封装 - 包含超时控制和异常处理"""
    
    def __init__(self, timeout=30):
        """
        初始化AI服务
        :param timeout: 请求超时时间（秒），默认30秒
        """
        self.timeout = timeout
        self.client = OpenAI(
            api_key=settings.AI_API_KEY,
            base_url=settings.AI_BASE_URL,
            timeout=timeout,  # 设置全局超时
            max_retries=0,    # 关闭自动重试，由调用方控制
        )
        self.model = settings.AI_MODEL

    def chat_stream(self, messages):
        """
        流式对话生成 - 带超时和异常处理
        :param messages: 消息列表 [{"role": "user", "content": "你好"}]
        :yield: 逐字返回的文本片段，或抛出异常
        """
        try:
            # 创建流式请求
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                stream=True,  # 开启流式返回
                timeout=self.timeout,
            )

            for chunk in response:
                # chunk.choices[0].delta.content 是增量文本
                content = chunk.choices[0].delta.content
                if content:
                    # yield：Python生成器，每次产生一个文本片段
                    yield content
                    
        except APITimeoutError as e:
            # 超时错误 - 向上抛出，让视图层处理
            raise TimeoutError(f"AI模型响应超时（{self.timeout}秒）")
            
        except RateLimitError as e:
            # 速率限制错误
            raise Exception(f"API速率限制，请稍后再试: {str(e)}")
            
        except APIError as e:
            # OpenAI API 错误
            raise Exception(f"AI服务错误: {str(e)}")
            
        except Exception as e:
            # 其他未知错误
            raise Exception(f"未知错误: {str(e)}")

    def generate_summary(self, content, max_length=200):
        """
        生成文章摘要 - 带超时和异常处理
        :param content: 文章内容
        :param max_length: 摘要最大长度
        :return: 摘要文本
        :raises: TimeoutError, Exception
        """
        prompt = f"""请为以下文章生成摘要，要求：
        1. 不超过{max_length}字
        2. 包含文章核心观点
        3. 语言简洁通顺
        
        文章内容：
        {content[:3000]}  # 只取前3000字，控制Token
    
        摘要："""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                stream=False,
                max_tokens=300,
                timeout=self.timeout,
            )
            return response.choices[0].message.content.strip()
        
        except APITimeoutError as e:
            raise TimeoutError(f"生成摘要超时（{self.timeout}秒）")
            
        except RateLimitError as e:
            raise Exception(f"API速率限制，请稍后再试")
            
        except APIError as e:
            raise Exception(f"AI服务错误: {str(e)}")
            
        except Exception as e:
            raise Exception(f"生成摘要失败: {str(e)}")

    def chat_with_retry(self, messages, max_retries=3, retry_delay=1):
        """
        带重试机制的聊天（非流式）
        :param messages: 消息列表
        :param max_retries: 最大重试次数
        :param retry_delay: 重试间隔（秒）
        :return: 完整回复文本
        """
        last_error = None
        
        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    stream=False,
                    timeout=self.timeout,
                )
                return response.choices[0].message.content.strip()
                
            except (APITimeoutError, APIError) as e:
                last_error = str(e)
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                break
                
        raise Exception(f"重试{max_retries}次后仍失败: {last_error}")
