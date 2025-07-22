import aiohttp
import asyncio
import json
from typing import List, Dict, Any, Callable, Optional, Union
import time

from .config_manager import ConfigManager

class LLMClient:
    """LLM客户端，处理与OpenAI API的交互"""
    
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.session = None
        self._semaphore = asyncio.Semaphore(3)  # 限制并发请求数
    
    async def _get_session(self):
        """获取或创建aiohttp会话"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def _make_request(self, url: str, headers: Dict[str, str], data: Dict[str, Any]) -> str:
        """发送HTTP请求"""
        async with self._semaphore:
            session = await self._get_session()
            try:
                async with session.post(url, headers=headers, json=data, timeout=60) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result['choices'][0]['message']['content']
                    else:
                        error_text = await response.text()
                        raise Exception(f"API请求失败: {response.status}, {error_text}")
            except asyncio.TimeoutError:
                raise Exception("API请求超时")
            except Exception as e:
                raise Exception(f"API请求异常: {str(e)}")
    
    async def _make_embedding_request(self, url: str, headers: Dict[str, str], texts: List[str]) -> List[List[float]]:
        """发送embedding请求"""
        async with self._semaphore:
            session = await self._get_session()
            try:
                data = {
                    "input": texts,
                    "model": "text-embedding-ada-002"
                }
                async with session.post(url, headers=headers, json=data, timeout=60) as response:
                    if response.status == 200:
                        result = await response.json()
                        return [item['embedding'] for item in result['data']]
                    else:
                        error_text = await response.text()
                        raise Exception(f"Embedding请求失败: {response.status}, {error_text}")
            except asyncio.TimeoutError:
                raise Exception("Embedding请求超时")
            except Exception as e:
                raise Exception(f"Embedding请求异常: {str(e)}")
    
    def create_llm_func(self, model_name: str) -> Callable:
        """创建LLM函数"""
        async def llm_func(
            prompt: str,
            system_prompt: str = None,
            history_messages: List[Dict[str, str]] = None,
            **kwargs
        ) -> str:
            openai_config = self.config_manager.get_openai_config()
            
            url = f"{openai_config['api_base']}/chat/completions"
            headers = self.config_manager.get_api_headers()
            
            # 构建消息
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            
            if history_messages:
                messages.extend(history_messages)
            
            messages.append({"role": "user", "content": prompt})
            
            # 构建请求数据
            data = {
                "model": model_name,
                "messages": messages,
                "temperature": openai_config.get('temperature', 0.1),
                "max_tokens": kwargs.get('max_tokens', 4000)
            }
            
            # 添加其他参数
            for key, value in kwargs.items():
                if key not in ['max_tokens']:
                    data[key] = value
            
            return await self._make_request(url, headers, data)
        
        return llm_func
    
    def create_embedding_func(self) -> Callable:
        """创建embedding函数"""
        async def embedding_func(texts: List[str]) -> List[List[float]]:
            if not texts:
                return []
            
            openai_config = self.config_manager.get_openai_config()
            url = f"{openai_config['api_base']}/embeddings"
            headers = self.config_manager.get_api_headers()
            
            # 分批处理，避免单次请求过大
            batch_size = 100
            all_embeddings = []
            
            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i:i + batch_size]
                embeddings = await self._make_embedding_request(url, headers, batch_texts)
                all_embeddings.extend(embeddings)
            
            return all_embeddings
        
        return embedding_func
    
    async def test_connection(self) -> Dict[str, Any]:
        """测试API连接"""
        try:
            openai_config = self.config_manager.get_openai_config()
            
            if not openai_config.get('api_key'):
                return {'success': False, 'error': 'API Key未配置'}
            
            url = f"{openai_config['api_base']}/chat/completions"
            headers = self.config_manager.get_api_headers()
            
            data = {
                "model": openai_config.get('qa_model', 'gpt-4o'),
                "messages": [{"role": "user", "content": "Hello"}],
                "max_tokens": 10
            }
            
            start_time = time.time()
            result = await self._make_request(url, headers, data)
            response_time = time.time() - start_time
            
            return {
                'success': True,
                'response_time': round(response_time, 2),
                'model': openai_config.get('qa_model', 'gpt-4o'),
                'response': result[:50] + '...' if len(result) > 50 else result
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def test_connection(self) -> bool:
        """同步测试连接"""
        try:
            # 从config_manager获取配置
            openai_config = self.config_manager.get_openai_config()
            base_url = openai_config.get('api_base', 'https://api.openai.com/v1')
            api_key = openai_config.get('api_key', '')
            
            if not api_key:
                return False
                
            # 创建一个简单的测试请求
            import requests
            
            url = f"{base_url}/chat/completions"
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
            
            data = {
                "model": "gpt-3.5-turbo",
                "messages": [{"role": "user", "content": "Hello"}],
                "max_tokens": 5
            }
            
            response = requests.post(url, headers=headers, json=data, timeout=10)
            return response.status_code == 200
            
        except Exception as e:
            print(f"连接测试失败: {e}")
            return False
    
    async def chat_completion_async(self, messages, model="gpt-3.5-turbo", **kwargs):
        """异步聊天完成"""
        try:
            if not self.session:
                import aiohttp
                self.session = aiohttp.ClientSession()
            
            url = f"{self.base_url}/chat/completions"
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            data = {
                "model": model,
                "messages": messages,
                **kwargs
            }
            
            async with self.session.post(url, headers=headers, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    return {
                        "content": result["choices"][0]["message"]["content"],
                        "usage": result.get("usage", {})
                    }
                else:
                    error_text = await response.text()
                    raise Exception(f"API错误: {response.status} - {error_text}")
                    
        except Exception as e:
            raise Exception(f"聊天完成失败: {str(e)}")

    async def close(self):
        """关闭客户端"""
        if self.session and not self.session.closed:
            await self.session.close() 