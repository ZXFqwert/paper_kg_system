import os
import json
import asyncio
import aiohttp
import feedparser
from datetime import datetime
from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
import threading
import uuid
from typing import Dict, List, Optional

from core.paper_manager import PaperManager
from core.graphrag_manager import GraphRAGManager
from core.config_manager import ConfigManager
from core.arxiv_client import ArxivClient

app = Flask(__name__)
CORS(app)

# 全局管理器实例
config_manager = ConfigManager()
paper_manager = PaperManager()
graphrag_manager = GraphRAGManager(config_manager)
arxiv_client = ArxivClient()

# 存储异步任务状态
task_status = {}

def run_async(coro):
    """在新的事件循环中运行协程"""
    def run_in_thread():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()
    
    thread = threading.Thread(target=run_in_thread)
    thread.start()
    return thread

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)

# ==================== 论文搜索相关API ====================

@app.route('/api/search', methods=['POST'])
def search_papers():
    """搜索ArXiv论文"""
    try:
        data = request.json
        query = data.get('query', '')
        start = data.get('start', 0)
        max_results = data.get('max_results', 10)
        sort_by = data.get('sort_by', 'relevance')
        
        if not query.strip():
            return jsonify({'error': '搜索关键词不能为空'}), 400
        
        # 调用ArXiv客户端搜索
        config = config_manager.get_config()
        deep_mode = config.get('deep_mode', False)
        
        result = arxiv_client.search_papers(
            query=query,
            start=start,
            max_results=max_results,
            sort_by=sort_by,
            deep_mode=deep_mode
        )
        
        # 检查论文收录状态
        for paper in result['papers']:
            paper['is_collected'] = paper_manager.is_paper_collected(paper['id'])
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': f'搜索失败: {str(e)}'}), 500

@app.route('/api/collect_paper', methods=['POST'])
def collect_paper():
    """收录论文"""
    try:
        data = request.json
        paper_data = data.get('paper_data', {})
        
        if not paper_data or not paper_data.get('id'):
            return jsonify({'error': '论文数据不完整'}), 400
        
        # 检查是否已收录
        if paper_manager.is_paper_collected(paper_data['id']):
            return jsonify({'error': '论文已收录'}), 400
        
        # 收录论文
        config = config_manager.get_config()
        deep_mode = config.get('deep_mode', False)
        
        success = paper_manager.collect_paper(paper_data, deep_mode)
        
        if success:
            return jsonify({'message': '论文收录成功'})
        else:
            return jsonify({'error': '论文收录失败'}), 500
            
    except Exception as e:
        return jsonify({'error': f'收录失败: {str(e)}'}), 500

@app.route('/api/paper_details/<paper_id>')
def get_paper_details(paper_id):
    """获取论文详细信息"""
    try:
        # 先从本地查找
        paper_data = paper_manager.get_paper_data(paper_id)
        
        if not paper_data:
            # 从ArXiv获取
            paper_data = arxiv_client.get_paper_details(paper_id)
            
        if paper_data:
            paper_data['is_collected'] = paper_manager.is_paper_collected(paper_id)
            return jsonify(paper_data)
        else:
            return jsonify({'error': '论文不存在'}), 404
            
    except Exception as e:
        return jsonify({'error': f'获取论文详情失败: {str(e)}'}), 500

# ==================== 知识图谱相关API ====================

@app.route('/api/collected_papers')
def get_collected_papers():
    """获取所有收录的论文"""
    try:
        papers = paper_manager.get_collected_papers()
        
        # 添加抽取状态信息
        for paper in papers:
            extraction_progress = graphrag_manager.get_extraction_progress(paper['id'])
            paper['extraction_status'] = extraction_progress.get('status', 'not_extracted')
            paper['extraction_progress'] = extraction_progress.get('progress', 0)
            paper['extracted'] = extraction_progress.get('status') == 'completed'
        
        return jsonify(papers)
        
    except Exception as e:
        return jsonify({'error': f'获取收录论文失败: {str(e)}'}), 500

@app.route('/api/extract_paper/<paper_id>', methods=['POST'])
def extract_paper(paper_id):
    """抽取单个论文的实体关系"""
    try:
        # 检查论文是否存在
        paper_data = paper_manager.get_paper_data(paper_id)
        if not paper_data:
            return jsonify({'error': '论文不存在'}), 404
        
        # 检查配置
        config = config_manager.get_config()
        openai_config = config.get('openai', {})
        if not openai_config.get('api_key'):
            return jsonify({'error': '请先配置OpenAI API Key'}), 400
        
        # 创建异步任务
        task_id = str(uuid.uuid4())
        
        async def extraction_task():
            try:
                success = await graphrag_manager.extract_paper(paper_id, paper_data)
                if success:
                    task_status[task_id] = {'status': 'completed', 'message': '抽取完成'}
                else:
                    task_status[task_id] = {'status': 'failed', 'message': '抽取失败'}
            except Exception as e:
                task_status[task_id] = {'status': 'failed', 'message': f'抽取失败: {str(e)}'}
        
        # 初始化任务状态
        task_status[task_id] = {'status': 'started', 'message': '开始抽取...'}
        
        # 在后台运行抽取任务
        run_async(extraction_task())
        
        return jsonify({'task_id': task_id, 'message': '抽取任务已启动'})
        
    except Exception as e:
        return jsonify({'error': f'启动抽取任务失败: {str(e)}'}), 500

@app.route('/api/extraction_progress/<paper_id>')
def get_extraction_progress(paper_id):
    """获取论文抽取进度"""
    try:
        progress = graphrag_manager.get_extraction_progress(paper_id)
        if not progress:
            return jsonify({'status': 'not_started', 'progress': 0})
        
        return jsonify({
            'status': progress.status,
            'progress': progress.progress,
            'current_step': progress.current_step,
            'error_message': progress.error_message
        })
        
    except Exception as e:
        return jsonify({'error': f'获取抽取进度失败: {str(e)}'}), 500

@app.route('/api/build_graph', methods=['POST'])
def build_knowledge_graph():
    """构建知识图谱"""
    try:
        # 检查配置
        config = config_manager.get_config()
        openai_config = config.get('openai', {})
        if not openai_config.get('api_key'):
            return jsonify({'error': '请先配置OpenAI API Key'}), 400
        
        # 检查是否有已抽取的论文
        extracted_papers = [p for p in paper_manager.get_collected_papers() 
                           if graphrag_manager.get_extraction_progress(p['id']).get('status') == 'completed']
        
        if not extracted_papers:
            return jsonify({'error': '没有已抽取的论文，请先抽取论文'}), 400
        
        # 创建异步任务
        task_id = str(uuid.uuid4())
        
        async def build_task():
            try:
                success = await graphrag_manager.build_knowledge_graph()
                if success:
                    task_status[task_id] = {'status': 'completed', 'message': '知识图谱构建完成'}
                else:
                    task_status[task_id] = {'status': 'failed', 'message': '知识图谱构建失败'}
            except Exception as e:
                task_status[task_id] = {'status': 'failed', 'message': f'构建失败: {str(e)}'}
        
        # 初始化任务状态
        task_status[task_id] = {'status': 'started', 'message': '开始构建知识图谱...'}
        
        # 在后台运行构建任务
        run_async(build_task())
        
        return jsonify({'task_id': task_id, 'message': '知识图谱构建任务已启动'})
        
    except Exception as e:
        return jsonify({'error': f'启动构建任务失败: {str(e)}'}), 500

@app.route('/api/build_progress')
def get_build_progress():
    """获取知识图谱构建进度"""
    try:
        progress = graphrag_manager.get_build_progress()
        return jsonify(progress)
        
    except Exception as e:
        return jsonify({'error': f'获取构建进度失败: {str(e)}'}), 500

@app.route('/api/query', methods=['POST'])
def query_knowledge_graph():
    """查询知识图谱"""
    try:
        data = request.json
        question = data.get('question', '')
        mode = data.get('mode', 'local')  # local 或 global
        
        if not question.strip():
            return jsonify({'error': '问题不能为空'}), 400
        
        # 检查配置
        config = config_manager.get_config()
        openai_config = config.get('openai', {})
        if not openai_config.get('api_key'):
            return jsonify({'error': '请先配置OpenAI API Key'}), 400
        
        # 异步查询
        async def query_task():
            return await graphrag_manager.query(question, mode)
        
        # 运行查询
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            answer = loop.run_until_complete(query_task())
            return jsonify({'answer': answer})
        finally:
            loop.close()
        
    except Exception as e:
        return jsonify({'error': f'查询失败: {str(e)}'}), 500

@app.route('/api/graph_stats')
def get_graph_stats():
    """获取知识图谱统计信息"""
    try:
        stats = graphrag_manager.get_graph_stats()
        return jsonify(stats)
        
    except Exception as e:
        return jsonify({'error': f'获取图谱统计失败: {str(e)}'}), 500

@app.route('/api/clear_data', methods=['POST'])
def clear_all_data():
    """清空所有数据"""
    try:
        # 清空论文数据
        paper_success = paper_manager.clear_all_papers()
        
        # 清空图数据
        graph_success = graphrag_manager.clear_all_data()
        
        if paper_success and graph_success:
            return jsonify({'message': '所有数据已清空'})
        else:
            return jsonify({'error': '清空数据时出现问题'}), 500
            
    except Exception as e:
        return jsonify({'error': f'清空数据失败: {str(e)}'}), 500

# ==================== 系统设置相关API ====================

@app.route('/api/config')
def get_config():
    """获取系统配置"""
    try:
        config = config_manager.get_config()
        # 创建安全的配置副本，返回掩码后的API密钥
        safe_config = config.copy()
        if 'openai' in safe_config and 'api_key' in safe_config['openai']:
            api_key = safe_config['openai']['api_key']
            if api_key:
                # 显示前4个字符和后4个字符，中间用*号替代
                if len(api_key) > 8:
                    safe_config['openai']['api_key'] = api_key[:4] + '*' * (len(api_key) - 8) + api_key[-4:]
                else:
                    safe_config['openai']['api_key'] = '*' * len(api_key)
            safe_config['has_api_key'] = bool(api_key)
        else:
            safe_config['has_api_key'] = False
        return jsonify(safe_config)
        
    except Exception as e:
        return jsonify({'error': f'获取配置失败: {str(e)}'}), 500

@app.route('/api/config', methods=['POST'])
def update_config():
    """更新系统配置"""
    try:
        data = request.json
        
        # 验证必要字段
        if data.get('openai', {}).get('api_key') is not None and not data['openai']['api_key'].strip():
            return jsonify({'error': 'OpenAI API Key不能为空'}), 400
        
        # 更新配置
        success = config_manager.update_config(data)
        
        if success:
            return jsonify({'message': '配置更新成功'})
        else:
            return jsonify({'error': '配置更新失败'}), 500
            
    except Exception as e:
        return jsonify({'error': f'更新配置失败: {str(e)}'}), 500

@app.route('/api/test_openai', methods=['POST'])
def test_openai_connection():
    """测试OpenAI连接"""
    try:
        from core.llm_client import LLMClient
        
        data = request.json or {}
        
        # 使用已保存的配置进行测试
        config = config_manager.get_config()
        openai_config = config.get('openai', {})
        
        if not openai_config.get('api_key'):
            return jsonify({'error': '请先配置并保存OpenAI API Key'}), 400
        
        llm_client = LLMClient(config_manager)
        
        # 测试连接
        success = llm_client.test_connection()
        
        if success:
            return jsonify({'message': 'OpenAI连接测试成功'})
        else:
            return jsonify({'error': 'OpenAI连接测试失败'}), 500
            
    except Exception as e:
        return jsonify({'error': f'连接测试失败: {str(e)}'}), 500

@app.route('/api/system_status')
def get_system_status():
    """获取系统状态"""
    try:
        papers = paper_manager.get_collected_papers()
        graph_stats = graphrag_manager.get_graph_stats()
        
        status = {
            'collected_papers': len(papers),
            'extracted_papers': len([p for p in papers 
                                   if graphrag_manager.get_extraction_progress(p['id']).get('status') == 'completed']),
            'entities_count': graph_stats.get('entities', 0),
            'relationships_count': graph_stats.get('relationships', 0),
            'communities_count': graph_stats.get('communities', 0),
            'storage_usage': _get_storage_usage(),
            'last_updated': datetime.now().isoformat()
        }
        
        return jsonify(status)
        
    except Exception as e:
        return jsonify({'error': f'获取系统状态失败: {str(e)}'}), 500

def _get_storage_usage():
    """计算存储空间使用情况"""
    try:
        total_size = 0
        data_dir = 'data'
        
        if os.path.exists(data_dir):
            for dirpath, dirnames, filenames in os.walk(data_dir):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    if os.path.exists(filepath):
                        total_size += os.path.getsize(filepath)
        
        # 转换为MB
        size_mb = total_size / (1024 * 1024)
        return f"{size_mb:.2f} MB"
        
    except:
        return "未知"

@app.route('/api/task_status/<task_id>')
def get_task_status(task_id):
    """获取任务状态"""
    try:
        status = task_status.get(task_id, {'status': 'not_found', 'message': '任务不存在'})
        return jsonify(status)
        
    except Exception as e:
        return jsonify({'error': f'获取任务状态失败: {str(e)}'}), 500

# ==================== 错误处理 ====================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': '接口不存在'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': '服务器内部错误'}), 500

if __name__ == '__main__':
    # 确保数据目录存在
    os.makedirs('data', exist_ok=True)
    os.makedirs('data/papers', exist_ok=True)
    os.makedirs('data/graph', exist_ok=True)
    
    print("=== 论文知识图谱系统 ===")
    print("启动中...")
    print("访问地址: http://localhost:5000")
    print("首次使用请先进入'系统设置'配置OpenAI API")
    
    app.run(debug=True, host='0.0.0.0', port=5000) 