import json
import os
from typing import Dict, Any

class ConfigManager:
    """系统配置管理器"""
    
    def __init__(self, config_file='data/config.json'):
        self.config_file = config_file
        self.default_config = {
            'openai': {
                'api_base': 'https://api.openai.com/v1',
                'api_key': '',
                'extract_model': 'gpt-4o-mini',
                'qa_model': 'gpt-4o',
                'temperature': 0.1
            },
            'system': {
                'deep_mode': False,
                'max_concurrent_extractions': 3,
                'chunk_size': 1200,
                'chunk_overlap': 100
            },
            'graph': {
                'entity_extract_max_gleaning': 1,
                'entity_summary_to_max_tokens': 500,
                'community_report_max_tokens': 15000
            }
        }
        self._load_config()
    
    def _load_config(self):
        """加载配置文件"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
                # 合并默认配置（处理新增配置项）
                self._merge_default_config()
            except Exception as e:
                print(f"配置文件加载失败，使用默认配置: {e}")
                self.config = self.default_config.copy()
        else:
            self.config = self.default_config.copy()
            self._save_config()
    
    def _merge_default_config(self):
        """合并默认配置，确保所有必要配置项都存在"""
        def merge_dict(default: dict, current: dict) -> dict:
            for key, value in default.items():
                if key not in current:
                    current[key] = value
                elif isinstance(value, dict) and isinstance(current[key], dict):
                    merge_dict(value, current[key])
            return current
        
        self.config = merge_dict(self.default_config, self.config)
    
    def _save_config(self) -> bool:
        """保存配置到文件"""
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"配置文件保存失败: {e}")
            return False
    
    def get_config(self) -> Dict[str, Any]:
        """获取完整配置"""
        return self.config.copy()
    
    def get_openai_config(self) -> Dict[str, str]:
        """获取OpenAI配置"""
        return self.config['openai'].copy()
    
    def get_system_config(self) -> Dict[str, Any]:
        """获取系统配置"""
        return self.config['system'].copy()
    
    def get_graph_config(self) -> Dict[str, Any]:
        """获取图配置"""
        return self.config['graph'].copy()
    
    def update_config(self, new_config: Dict[str, Any]) -> bool:
        """更新配置"""
        try:
            def update_dict(target: dict, source: dict):
                for key, value in source.items():
                    if key in target:
                        if isinstance(value, dict) and isinstance(target[key], dict):
                            update_dict(target[key], value)
                        else:
                            target[key] = value
                    else:
                        # 如果是顶级配置项，直接添加
                        if target is self.config:
                            target[key] = value
            
            update_dict(self.config, new_config)
            return self._save_config()
        except Exception as e:
            print(f"配置更新失败: {e}")
            return False
    
    def validate_openai_config(self) -> bool:
        """验证OpenAI配置是否完整"""
        openai_config = self.config['openai']
        return bool(openai_config.get('api_key') and openai_config.get('api_base'))
    
    def get_api_headers(self) -> Dict[str, str]:
        """获取API请求头"""
        return {
            'Authorization': f"Bearer {self.config['openai']['api_key']}",
            'Content-Type': 'application/json'
        } 