"""
LLM 客户端 - 支持任何兼容 OpenAI API 的本地模型

配置示例：
llm:
  api_base: http://localhost:11434/v1  # Ollama
  api_key: ""
  model: qwen2.5:14b
  timeout: 60
  max_tokens: 4096
  temperature: 0.7
"""

import requests
import aiohttp
from typing import Optional, Dict, List
from loguru import logger


class LLMClient:
    """
    LLM 客户端
    
    支持任何兼容 OpenAI Chat Completions API 的服务：
    - Ollama (http://localhost:11434/v1)
    - LocalAI (http://localhost:8080/v1)
    - vLLM (http://localhost:8000/v1)
    - OpenAI (https://api.openai.com/v1)
    - 智谱 AI (https://open.bigmodel.cn/api/paas/v4)
    """
    
    def __init__(self, config: dict):
        """
        初始化 LLM 客户端
        
        Args:
            config: LLM 配置字典
        """
        self.api_base = config.get('api_base', 'http://localhost:11434/v1')
        self.api_key = config.get('api_key', '')
        self.model = config.get('model', 'qwen2.5:14b')
        self.timeout = config.get('timeout', 60)
        self.max_tokens = config.get('max_tokens', 4096)
        self.temperature = config.get('temperature', 0.7)
        
        logger.info(f"LLM 客户端初始化: {self.api_base} ({self.model})")
    
    def chat(self, prompt: str, system_prompt: str = None) -> str:
        """
        同步调用 LLM
        
        Args:
            prompt: 用户提示
            system_prompt: 系统提示（可选）
        
        Returns:
            LLM 响应文本
        """
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": prompt})
        
        headers = {
            "Content-Type": "application/json"
        }
        
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature
        }
        
        try:
            response = requests.post(
                f"{self.api_base}/chat/completions",
                headers=headers,
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            result = response.json()
            
            content = result['choices'][0]['message']['content']
            logger.debug(f"LLM 响应长度: {len(content)} 字符")
            
            return content
            
        except requests.exceptions.Timeout:
            logger.error(f"LLM 请求超时 ({self.timeout}s)")
            raise RuntimeError(f"LLM 请求超时 ({self.timeout}s)")
        
        except requests.exceptions.RequestException as e:
            logger.error(f"LLM 请求失败: {e}")
            raise RuntimeError(f"LLM 请求失败: {e}")
        
        except (KeyError, IndexError) as e:
            logger.error(f"LLM 响应格式错误: {e}")
            raise RuntimeError(f"LLM 响应格式错误: {e}")
    
    async def chat_async(self, prompt: str, system_prompt: str = None) -> str:
        """
        异步调用 LLM
        
        Args:
            prompt: 用户提示
            system_prompt: 系统提示（可选）
        
        Returns:
            LLM 响应文本
        """
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": prompt})
        
        headers = {
            "Content-Type": "application/json"
        }
        
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_base}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    response.raise_for_status()
                    result = await response.json()
                    
                    content = result['choices'][0]['message']['content']
                    logger.debug(f"LLM 响应长度: {len(content)} 字符")
                    
                    return content
                    
        except aiohttp.ClientError as e:
            logger.error(f"LLM 异步请求失败: {e}")
            raise RuntimeError(f"LLM 异步请求失败: {e}")
        
        except (KeyError, IndexError) as e:
            logger.error(f"LLM 响应格式错误: {e}")
            raise RuntimeError(f"LLM 响应格式错误: {e}")
    
    def chat_with_history(self, messages: List[Dict]) -> str:
        """
        带历史记录的对话
        
        Args:
            messages: 消息列表 [{"role": "user/assistant", "content": "..."}]
        
        Returns:
            LLM 响应文本
        """
        headers = {
            "Content-Type": "application/json"
        }
        
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature
        }
        
        try:
            response = requests.post(
                f"{self.api_base}/chat/completions",
                headers=headers,
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            result = response.json()
            
            return result['choices'][0]['message']['content']
            
        except Exception as e:
            logger.error(f"LLM 请求失败: {e}")
            raise RuntimeError(f"LLM 请求失败: {e}")