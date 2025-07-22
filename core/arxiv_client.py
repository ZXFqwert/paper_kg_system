import requests
import feedparser
import re
import time
from typing import Dict, List, Optional, Any
from urllib.parse import quote


class ArxivClient:
    """ArXiv API客户端"""
    
    def __init__(self):
        self.base_url = "http://export.arxiv.org/api/query"
        self.max_results_per_query = 100
    
    def search_papers(
        self, 
        query: str, 
        start: int = 0, 
        max_results: int = 10,
        sort_by: str = "relevance",
        deep_mode: bool = False
    ) -> Dict[str, Any]:
        """
        搜索论文
        
        Args:
            query: 搜索关键词
            start: 起始位置
            max_results: 最大结果数
            sort_by: 排序方式 (relevance, lastUpdatedDate, submittedDate)
            deep_mode: 是否获取完整内容
        
        Returns:
            包含论文列表和分页信息的字典
        """
        try:
            # 构建查询参数
            params = {
                'search_query': f'all:{query}',
                'start': start,
                'max_results': min(max_results, self.max_results_per_query),
                'sortBy': sort_by,
                'sortOrder': 'descending'
            }
            
            # 发送请求
            response = requests.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            
            # 解析RSS响应
            feed = feedparser.parse(response.content)
            
            papers = []
            for entry in feed.entries:
                paper = self._parse_paper_entry(entry, deep_mode)
                if paper:
                    papers.append(paper)
            
            # 计算分页信息
            total_results = getattr(feed.feed, 'opensearch_totalresults', len(papers))
            total_results = int(total_results) if total_results else len(papers)
            
            return {
                'papers': papers,
                'total_results': total_results,
                'start': start,
                'max_results': max_results,
                'has_next': start + max_results < total_results,
                'has_prev': start > 0
            }
            
        except requests.RequestException as e:
            print(f"网络请求失败: {e}")
            return {
                'papers': [],
                'total_results': 0,
                'start': start,
                'max_results': max_results,
                'has_next': False,
                'has_prev': False,
                'error': f"网络请求失败: {str(e)}"
            }
        except Exception as e:
            print(f"解析失败: {e}")
            return {
                'papers': [],
                'total_results': 0,
                'start': start,
                'max_results': max_results,
                'has_next': False,
                'has_prev': False,
                'error': f"解析失败: {str(e)}"
            }
    
    def _parse_paper_entry(self, entry, deep_mode: bool = False) -> Optional[Dict[str, Any]]:
        """解析单个论文条目"""
        try:
            # 提取ID
            arxiv_id = entry.id.split('/')[-1]
            if 'v' in arxiv_id:
                arxiv_id = arxiv_id.split('v')[0]
            
            # 提取作者
            authors = []
            if hasattr(entry, 'authors'):
                authors = [author.name for author in entry.authors]
            elif hasattr(entry, 'author'):
                authors = [entry.author]
            
            # 提取分类
            categories = []
            if hasattr(entry, 'tags'):
                categories = [tag.term for tag in entry.tags]
            
            # 提取链接
            pdf_link = None
            arxiv_link = None
            if hasattr(entry, 'links'):
                for link in entry.links:
                    if link.type == 'application/pdf':
                        pdf_link = link.href
                    elif 'abs' in link.href:
                        arxiv_link = link.href
            
            # 基本论文信息
            paper = {
                'id': arxiv_id,
                'title': entry.title.replace('\n', ' ').strip(),
                'authors': authors,
                'summary': entry.summary.replace('\n', ' ').strip(),
                'abstract': entry.summary.replace('\n', ' ').strip(),  # 前端期望的字段名
                'published': entry.published,
                'updated': getattr(entry, 'updated', entry.published),
                'categories': categories,
                'pdf_link': pdf_link,
                'pdf_url': pdf_link,  # 前端期望的字段名
                'arxiv_link': arxiv_link,
                'arxiv_url': arxiv_link,  # 前端期望的字段名
                'keywords': self._extract_keywords(entry.summary + ' ' + entry.title)
            }
            
            # 深度模式：获取完整论文内容
            if deep_mode:
                paper['full_content'] = self._get_full_content(arxiv_id, pdf_link)
            
            return paper
            
        except Exception as e:
            print(f"解析论文条目失败: {e}")
            return None
    
    def _extract_keywords(self, text: str) -> List[str]:
        """从文本中提取关键词"""
        # 简单的关键词提取逻辑
        # 这里可以使用更复杂的NLP技术
        common_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those',
            'we', 'us', 'our', 'ours', 'you', 'your', 'yours'
        }
        
        # 提取单词，过滤常见词
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        keywords = [word for word in words if word not in common_words]
        
        # 统计词频并返回前10个
        from collections import Counter
        word_counts = Counter(keywords)
        return [word for word, count in word_counts.most_common(10)]
    
    def _get_full_content(self, arxiv_id: str, pdf_link: str) -> str:
        """获取论文完整内容（深度模式）"""
        try:
            if not pdf_link:
                return ""
            
            # 这里应该实现PDF下载和文本提取
            # 由于复杂性，这里先返回摘要
            # 在实际实现中，可以使用PyMuPDF或其他PDF处理库
            print(f"深度模式：需要处理PDF {pdf_link}")
            return ""
            
        except Exception as e:
            print(f"获取完整内容失败: {e}")
            return ""
    
    def get_paper_details(self, arxiv_id: str) -> Optional[Dict[str, Any]]:
        """获取单个论文的详细信息"""
        try:
            result = self.search_papers(f"id:{arxiv_id}", max_results=1)
            if result['papers']:
                return result['papers'][0]
            return None
        except Exception as e:
            print(f"获取论文详情失败: {e}")
            return None 