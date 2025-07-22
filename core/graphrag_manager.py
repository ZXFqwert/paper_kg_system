import asyncio
import os
import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass

# 导入nano-graphrag核心模块
from .nano_graphrag import GraphRAG, QueryParam


@dataclass
class ExtractionProgress:
    """抽取进度跟踪"""
    paper_id: str
    paper_title: str
    current_step: str
    progress: float
    status: str  # 'processing', 'completed', 'error'
    error_message: Optional[str] = None


class GraphRAGManager:
    """GraphRAG知识图谱管理器"""
    
    def __init__(self, config_manager, data_dir='data/graph'):
        self.config_manager = config_manager
        self.data_dir = data_dir
        self.graph_data_dir = os.path.join(data_dir, 'graphrag')
        
        # 确保目录存在
        os.makedirs(self.graph_data_dir, exist_ok=True)
        
        # 初始化GraphRAG实例
        self.graphrag = None
        self.is_initialized = False
        self.extraction_progress = {}
        self.build_progress = {"status": "idle", "progress": 0, "message": ""}
        
        # 异步锁
        self._extraction_lock = asyncio.Lock()
        self._build_lock = asyncio.Lock()
    
    def _get_llm_config(self) -> Dict[str, Any]:
        """获取LLM配置"""
        config = self.config_manager.get_config()
        openai_config = config.get('openai', {})
        
        # OpenAI API配置
        llm_config = {
            "model": openai_config.get("extract_model", "gpt-3.5-turbo"),
            "api_key": openai_config.get("api_key", ""),
            "base_url": openai_config.get("api_base", "https://api.openai.com/v1"),
            "temperature": openai_config.get("temperature", 0.1),
            "max_tokens": 4000,
        }
        
        return llm_config
    
    async def _create_llm_func(self, model_name: str = None) -> Callable:
        """创建LLM调用函数"""
        from .llm_client import LLMClient
        
        config = self._get_llm_config()
        if model_name:
            config["model"] = model_name
            
        llm_client = LLMClient(self.config_manager)
        
        async def llm_func(
            prompt: str, 
            system_prompt: str = None, 
            max_tokens: int = None,
            **kwargs
        ) -> str:
            """异步LLM调用函数"""
            try:
                response = await llm_client.chat_completion_async(
                    messages=[
                        {"role": "system", "content": system_prompt or "You are a helpful assistant."},
                        {"role": "user", "content": prompt}
                    ],
                    model=config["model"],
                    temperature=config["temperature"],
                    max_tokens=max_tokens or config["max_tokens"],
                    **kwargs
                )
                return response.get("content", "")
            except Exception as e:
                print(f"LLM调用失败: {e}")
                return f"错误: {str(e)}"
        
        return llm_func
    
    def _initialize_graphrag(self):
        """初始化GraphRAG实例"""
        try:
            if self.is_initialized:
                return True
                
            # 设置OpenAI环境变量，供nano-graphrag使用
            config = self.config_manager.get_config()
            openai_config = config.get('openai', {})
            
            print(f"设置环境变量前 - API Key: {openai_config.get('api_key', 'None')[:10]}...")
            print(f"设置环境变量前 - API Base: {openai_config.get('api_base', 'None')}")
            
            if openai_config.get('api_key'):
                os.environ['OPENAI_API_KEY'] = openai_config['api_key']
                print(f"已设置 OPENAI_API_KEY: {os.environ.get('OPENAI_API_KEY', 'None')[:10]}...")
            if openai_config.get('api_base'):
                os.environ['OPENAI_BASE_URL'] = openai_config['api_base']
                print(f"已设置 OPENAI_BASE_URL: {os.environ.get('OPENAI_BASE_URL', 'None')}")
                
            # 强制重新创建OpenAI客户端以使用新的环境变量
            from .nano_graphrag import _llm
            _llm.global_openai_async_client = None
            print("已重置全局OpenAI客户端，将使用新的环境变量")
                
            # 配置存储
            working_dir = self.graph_data_dir
            
            # 创建GraphRAG实例，让它自己处理存储初始化
            self.graphrag = GraphRAG(
                working_dir=working_dir,
                enable_llm_cache=True,
            )
            
            self.is_initialized = True
            return True
            
        except Exception as e:
            print(f"GraphRAG初始化失败: {e}")
            return False
    
    async def extract_paper(self, paper_id: str, paper_data: Dict[str, Any]) -> bool:
        """异步抽取单个论文的实体和关系"""
        async with self._extraction_lock:
            try:
                # 初始化进度跟踪
                self.extraction_progress[paper_id] = ExtractionProgress(
                    paper_id=paper_id,
                    paper_title=paper_data.get('title', 'Unknown'),
                    current_step="准备中...",
                    progress=0.0,
                    status="processing"
                )
                
                # 确保GraphRAG已初始化
                if not self._initialize_graphrag():
                    raise Exception("GraphRAG初始化失败")
                
                # 准备文档内容
                content = self._prepare_document_content(paper_data)
                if not content.strip():
                    raise Exception("论文内容为空")
                
                # 更新进度
                self.extraction_progress[paper_id].current_step = "文本切分中..."
                self.extraction_progress[paper_id].progress = 0.2
                
                # 使用GraphRAG进行插入和处理
                await self.graphrag.ainsert(content)
                
                # 更新进度
                self.extraction_progress[paper_id].current_step = "实体抽取中..."
                self.extraction_progress[paper_id].progress = 0.6
                
                # 等待处理完成（这里可能需要轮询或其他机制）
                await asyncio.sleep(2)  # 模拟处理时间
                
                # 完成
                self.extraction_progress[paper_id].current_step = "完成"
                self.extraction_progress[paper_id].progress = 1.0
                self.extraction_progress[paper_id].status = "completed"
                
                return True
                
            except Exception as e:
                # 错误处理
                self.extraction_progress[paper_id].status = "error"
                self.extraction_progress[paper_id].error_message = str(e)
                print(f"论文抽取失败 {paper_id}: {e}")
                return False
    
    def _prepare_document_content(self, paper_data: Dict[str, Any]) -> str:
        """准备文档内容用于抽取"""
        config = self.config_manager.get_config()
        deep_mode = config.get("deep_mode", False)
        
        # 基础内容
        content_parts = [
            f"Title: {paper_data.get('title', '')}",
            f"Authors: {', '.join(paper_data.get('authors', []))}",
            f"Abstract: {paper_data.get('summary', '')}",
            f"Categories: {', '.join(paper_data.get('categories', []))}",
            f"Keywords: {', '.join(paper_data.get('keywords', []))}"
        ]
        
        # 深度模式：包含完整内容
        if deep_mode and 'full_content' in paper_data:
            content_parts.append(f"Full Content: {paper_data['full_content']}")
        
        return "\n\n".join(content_parts)
    
    async def build_knowledge_graph(self) -> bool:
        """构建完整的知识图谱"""
        async with self._build_lock:
            try:
                self.build_progress = {"status": "processing", "progress": 0.0, "message": "初始化..."}
                
                if not self._initialize_graphrag():
                    raise Exception("GraphRAG初始化失败")
                
                # 检查是否有数据
                from .nano_graphrag.base import QueryParam
                if not hasattr(self.graphrag, 'chunk_entity_relation_graph') or self.graphrag.chunk_entity_relation_graph is None:
                    raise Exception("没有找到已抽取的数据，请先抽取论文")
                
                # 社区检测
                self.build_progress = {"status": "processing", "progress": 0.3, "message": "执行社区检测..."}
                await self.graphrag.chunk_entity_relation_graph.clustering(
                    self.graphrag.graph_cluster_algorithm
                )
                
                # 生成社区摘要
                self.build_progress = {"status": "processing", "progress": 0.6, "message": "生成社区摘要..."}
                from .nano_graphrag._op import generate_community_report
                from dataclasses import asdict
                await generate_community_report(
                    self.graphrag.community_reports, 
                    self.graphrag.chunk_entity_relation_graph, 
                    asdict(self.graphrag)
                )
                
                # 完成构建
                self.build_progress = {"status": "processing", "progress": 0.9, "message": "完成构建..."}
                await asyncio.sleep(1)  # 等待最终处理
                
                self.build_progress = {"status": "completed", "progress": 1.0, "message": "知识图谱构建完成"}
                return True
                
            except Exception as e:
                self.build_progress = {"status": "error", "progress": 0.0, "message": f"构建失败: {str(e)}"}
                print(f"知识图谱构建失败: {e}")
                return False
    
    async def query(self, question: str, mode: str = "local") -> str:
        """查询知识图谱"""
        try:
            if not self._initialize_graphrag():
                return "知识图谱未初始化"
            
            # 检查数据是否存在
            if mode == "global":
                # 检查是否有社区报告
                try:
                    community_keys = await self.graphrag.community_reports.all_keys()
                    if not community_keys:
                        return "Global查询需要先构建知识图谱。请点击'构建知识图谱'按钮完成社区检测和摘要生成。"
                except Exception as e:
                    return f"检查社区报告失败: {str(e)}"
            
            # 使用GraphRAG查询
            if mode == "local":
                response = await self.graphrag.aquery(question, param=QueryParam(mode="local"))
            else:  # global
                response = await self.graphrag.aquery(question, param=QueryParam(mode="global"))
            
            return response
            
        except Exception as e:
            print(f"查询失败: {e}")
            return f"查询失败: {str(e)}"
    
    def get_extraction_progress(self, paper_id: str = None) -> Dict[str, Any]:
        """获取抽取进度"""
        if paper_id:
            progress_obj = self.extraction_progress.get(paper_id)
            if progress_obj:
                return {
                    'paper_id': progress_obj.paper_id,
                    'paper_title': progress_obj.paper_title,
                    'current_step': progress_obj.current_step,
                    'progress': progress_obj.progress,
                    'status': progress_obj.status,
                    'error_message': progress_obj.error_message
                }
            else:
                return {
                    'status': 'not_extracted',
                    'progress': 0,
                    'current_step': '未开始',
                    'error_message': None
                }
        
        # 返回所有进度，转换为字典格式
        result = {}
        for pid, progress_obj in self.extraction_progress.items():
            result[pid] = {
                'paper_id': progress_obj.paper_id,
                'paper_title': progress_obj.paper_title,
                'current_step': progress_obj.current_step,
                'progress': progress_obj.progress,
                'status': progress_obj.status,
                'error_message': progress_obj.error_message
            }
        return result
    
    def get_build_progress(self) -> Dict[str, Any]:
        """获取构建进度"""
        return self.build_progress
    
    def get_graph_stats(self) -> Dict[str, Any]:
        """获取图谱统计信息"""
        try:
            if not self.is_initialized:
                return {"entities": 0, "relationships": 0, "communities": 0}
            
            # 这里需要根据实际的存储实现来获取统计信息
            # 暂时返回模拟数据
            return {
                "entities": len(self.extraction_progress) * 10,  # 估算
                "relationships": len(self.extraction_progress) * 5,  # 估算
                "communities": max(1, len(self.extraction_progress) // 3)  # 估算
            }
            
        except Exception as e:
            print(f"获取图谱统计失败: {e}")
            return {"entities": 0, "relationships": 0, "communities": 0}
    
    def clear_all_data(self):
        """清空所有数据"""
        try:
            # 清空进度状态
            self.extraction_progress = {}
            self.build_progress = {"status": "idle", "progress": 0, "message": ""}
            
            # 删除图数据文件
            import shutil
            if os.path.exists(self.graph_data_dir):
                shutil.rmtree(self.graph_data_dir)
                os.makedirs(self.graph_data_dir, exist_ok=True)
            
            # 重置GraphRAG实例
            self.graphrag = None
            self.is_initialized = False
            
            return True
            
        except Exception as e:
            print(f"清空数据失败: {e}")
            return False 