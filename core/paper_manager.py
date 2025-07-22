import os
import json
import requests
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Any
import time

class PaperManager:
    """论文管理器"""
    
    def __init__(self, data_dir='data/papers'):
        self.data_dir = data_dir
        self.metadata_file = os.path.join(data_dir, 'metadata.json')
        os.makedirs(data_dir, exist_ok=True)
        self._load_metadata()
    
    def _load_metadata(self):
        """加载论文元数据"""
        if os.path.exists(self.metadata_file):
            try:
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    self.metadata = json.load(f)
            except Exception as e:
                print(f"元数据文件加载失败: {e}")
                self.metadata = {}
        else:
            self.metadata = {}
    
    def _save_metadata(self):
        """保存论文元数据"""
        try:
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"元数据文件保存失败: {e}")
    
    def is_paper_collected(self, paper_id: str) -> bool:
        """检查论文是否已收录"""
        return paper_id in self.metadata
    
    def collect_paper(self, paper_data: Dict[str, Any], deep_mode: bool = False) -> bool:
        """收录论文"""
        try:
            paper_id = paper_data['id']
            
            # 如果已收录，则更新信息
            if paper_id in self.metadata:
                self.metadata[paper_id].update({
                    'updated_at': datetime.now().isoformat(),
                    'deep_mode': deep_mode or self.metadata[paper_id].get('deep_mode', False)
                })
            else:
                # 新收录论文
                self.metadata[paper_id] = {
                    'id': paper_id,
                    'title': paper_data.get('title', ''),
                    'authors': paper_data.get('authors', []),
                    'abstract': paper_data.get('abstract', ''),
                    'published': paper_data.get('published', ''),
                    'categories': paper_data.get('categories', []),
                    'arxiv_url': paper_data.get('arxiv_url', ''),
                    'pdf_url': paper_data.get('pdf_url', ''),
                    'collected_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat(),
                    'deep_mode': deep_mode,
                    'extracted': False,  # 是否已抽取实体关系
                    'extraction_status': 'pending'  # pending, running, completed, failed
                }
            
            # 如果是深度模式，下载并保存完整论文文本
            if deep_mode:
                success = self._download_paper_content(paper_id, paper_data.get('pdf_url', ''))
                if not success:
                    print(f"论文 {paper_id} 的完整文本下载失败，仅保存元数据")
            
            self._save_metadata()
            return True
            
        except Exception as e:
            print(f"收录论文失败: {e}")
            return False
    
    def _download_paper_content(self, paper_id: str, pdf_url: str) -> bool:
        """下载论文完整内容（模拟，实际需要PDF解析）"""
        try:
            # 这里应该实现PDF下载和文本提取
            # 为简化示例，我们暂时使用摘要作为内容
            content_file = os.path.join(self.data_dir, f"{paper_id}_content.txt")
            
            # 模拟从PDF提取的文本内容
            if paper_id in self.metadata:
                content = f"""Title: {self.metadata[paper_id]['title']}

Abstract: {self.metadata[paper_id]['abstract']}

Authors: {', '.join(self.metadata[paper_id]['authors'])}

Categories: {', '.join(self.metadata[paper_id]['categories'])}

[注意: 在实际实现中，这里应该是从PDF提取的完整论文文本内容]
"""
                with open(content_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                self.metadata[paper_id]['content_file'] = content_file
                return True
            
        except Exception as e:
            print(f"下载论文内容失败: {e}")
            return False
    
    def get_collected_papers(self) -> List[Dict[str, Any]]:
        """获取所有收录的论文"""
        papers = []
        for paper_id, data in self.metadata.items():
            papers.append(data)
        return sorted(papers, key=lambda x: x['collected_at'], reverse=True)
    
    def get_paper_content(self, paper_id: str) -> Optional[str]:
        """获取论文内容"""
        if paper_id not in self.metadata:
            return None
        
        paper_data = self.metadata[paper_id]
        
        # 如果有完整内容文件
        if paper_data.get('content_file') and os.path.exists(paper_data['content_file']):
            try:
                with open(paper_data['content_file'], 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception as e:
                print(f"读取论文内容文件失败: {e}")
        
        # 否则返回元数据组合的内容
        content = f"""Title: {paper_data['title']}

Abstract: {paper_data['abstract']}

Authors: {', '.join(paper_data['authors'])}

Categories: {', '.join(paper_data['categories'])}

Published: {paper_data['published']}
"""
        return content
    
    def update_extraction_status(self, paper_id: str, status: str):
        """更新抽取状态"""
        if paper_id in self.metadata:
            self.metadata[paper_id]['extraction_status'] = status
            if status == 'completed':
                self.metadata[paper_id]['extracted'] = True
            self._save_metadata()
    
    def get_storage_info(self) -> Dict[str, Any]:
        """获取存储信息"""
        try:
            total_size = 0
            file_count = 0
            
            # 计算数据目录大小
            for root, dirs, files in os.walk(self.data_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    if os.path.exists(file_path):
                        total_size += os.path.getsize(file_path)
                        file_count += 1
            
            return {
                'used': round(total_size / (1024 * 1024), 2),  # MB
                'files': file_count,
                'papers': len(self.metadata)
            }
        except Exception as e:
            print(f"获取存储信息失败: {e}")
            return {'used': 0, 'files': 0, 'papers': 0}
    
    def get_papers_for_extraction(self) -> List[str]:
        """获取需要抽取的论文ID列表"""
        return [
            paper_id for paper_id, data in self.metadata.items()
            if not data.get('extracted', False) or data.get('extraction_status') == 'failed'
        ]
    
    def delete_paper(self, paper_id: str) -> bool:
        """删除论文"""
        try:
            if paper_id in self.metadata:
                paper_data = self.metadata[paper_id]
                
                # 删除内容文件
                if paper_data.get('content_file') and os.path.exists(paper_data['content_file']):
                    os.remove(paper_data['content_file'])
                
                # 删除元数据
                del self.metadata[paper_id]
                self._save_metadata()
                return True
            return False
        except Exception as e:
            print(f"删除论文失败: {e}")
            return False 
    
    def get_paper_data(self, paper_id: str) -> Optional[Dict[str, Any]]:
        """获取论文数据"""
        return self.metadata.get(paper_id)
    
    def clear_all_papers(self) -> bool:
        """清空所有论文数据"""
        try:
            # 删除所有内容文件
            for paper_data in self.metadata.values():
                if paper_data.get('content_file') and os.path.exists(paper_data['content_file']):
                    os.remove(paper_data['content_file'])
            
            # 清空元数据
            self.metadata = {}
            self._save_metadata()
            
            return True
        except Exception as e:
            print(f"清空论文数据失败: {e}")
            return False 