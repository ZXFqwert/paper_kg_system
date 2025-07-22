#!/usr/bin/env python3
"""
论文知识图谱系统演示脚本
"""

import os
import json
import sys

def create_demo_config():
    """创建演示配置"""
    config = {
        "openai": {
            "api_base": "https://api.huiyan-ai.cn/v1",
            "api_key": "sk-f9U3GL2EBMrvw524mgkLKqmRrjhdKWi05Bp5u1tAHcAbiSkC",
            "extract_model": "gpt-4.1",
            "qa_model": "gpt-4.1",
            "temperature": 0.1
        },
        "system": {
            "deep_mode": False,
            "max_concurrent_extractions": 3,
            "chunk_size": 1200,
            "chunk_overlap": 100
        },
        "graph": {
            "entity_extract_max_gleaning": 1,
            "entity_summary_to_max_tokens": 500,
            "community_report_max_tokens": 15000
        }
    }
    
    os.makedirs('data', exist_ok=True)
    with open('data/config.json', 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    print("✓ 演示配置已创建")

def create_demo_papers():
    """创建演示论文数据"""
    papers = {
        "2301.00001": {
            "id": "2301.00001",
            "title": "Attention Is All You Need",
            "authors": ["Ashish Vaswani", "Noam Shazeer", "Niki Parmar"],
            "abstract": "The dominant sequence transduction models are based on complex recurrent or convolutional neural networks...",
            "published": "2017-06-12T17:59:59Z",
            "categories": ["cs.CL", "cs.AI"],
            "arxiv_url": "http://arxiv.org/abs/1706.03762v5",
            "pdf_url": "http://arxiv.org/pdf/1706.03762v5.pdf",
            "collected_at": "2024-01-01T10:00:00",
            "updated_at": "2024-01-01T10:00:00",
            "deep_mode": False,
            "extracted": False,
            "extraction_status": "pending"
        },
        "2301.00002": {
            "id": "2301.00002", 
            "title": "BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding",
            "authors": ["Jacob Devlin", "Ming-Wei Chang", "Kenton Lee"],
            "abstract": "We introduce a new language representation model called BERT, which stands for Bidirectional Encoder Representations from Transformers...",
            "published": "2018-10-11T18:33:37Z",
            "categories": ["cs.CL"],
            "arxiv_url": "http://arxiv.org/abs/1810.04805v2",
            "pdf_url": "http://arxiv.org/pdf/1810.04805v2.pdf",
            "collected_at": "2024-01-01T10:05:00",
            "updated_at": "2024-01-01T10:05:00",
            "deep_mode": False,
            "extracted": False,
            "extraction_status": "pending"
        }
    }
    
    os.makedirs('data/papers', exist_ok=True)
    with open('data/papers/metadata.json', 'w', encoding='utf-8') as f:
        json.dump(papers, f, indent=2, ensure_ascii=False)
    
    print("✓ 演示论文数据已创建")

def print_usage_guide():
    """打印使用指南"""
    print("\n" + "="*60)
    print("📖 论文知识图谱系统使用指南")
    print("="*60)
    
    print("\n🚀 启动系统:")
    print("   python run.py")
    print("   或者: python app.py")
    
    print("\n🌐 访问地址:")
    print("   http://localhost:5000")
    
    print("\n⚙️ 首次使用设置:")
    print("   1. 访问'系统设置'页面")
    print("   2. 配置您的OpenAI API Key")
    print("   3. 设置API Base URL（如使用代理）")
    print("   4. 点击'测试连接'验证配置")
    
    print("\n📝 基本流程:")
    print("   1. 论文检索 -> 输入关键词搜索ArXiv论文")
    print("   2. 收录论文 -> 点击'收录'保存感兴趣的论文") 
    print("   3. 抽取实体 -> 在知识图谱页面点击'抽取'")
    print("   4. 构建图谱 -> 点击'构建知识图谱'")
    print("   5. 智能问答 -> 输入问题进行查询")
    
    print("\n💡 功能亮点:")
    print("   • 实时搜索ArXiv论文库")
    print("   • 自动实体关系抽取")
    print("   • Local/Global两种查询模式")
    print("   • 进度实时反馈")
    print("   • 现代化响应式界面")
    
    print("\n⚠️ 注意事项:")
    print("   • 需要有效的OpenAI API Key")
    print("   • 确保网络可访问ArXiv和OpenAI")
    print("   • 抽取和查询会消耗API tokens")
    print("   • 建议在稳定网络环境下使用")
    
    print("\n📁 数据存储:")
    print("   • data/papers/ - 论文数据")
    print("   • data/graph/ - 知识图谱数据")
    print("   • data/config.json - 系统配置")
    
    print("\n🔧 故障排除:")
    print("   • 检查API配置是否正确")
    print("   • 确认网络连接正常")
    print("   • 查看控制台错误信息")
    print("   • 重启应用重新加载配置")

def main():
    print("🎯 论文知识图谱系统演示初始化")
    print("-" * 40)
    
    # 检查当前目录
    if not os.path.exists('app.py'):
        print("❌ 请在项目根目录运行此脚本")
        return
    
    # 创建演示数据
    create_demo_config()
    create_demo_papers()
    
    print("\n✅ 演示环境初始化完成!")
    
    # 显示使用指南
    print_usage_guide()
    
    print("\n" + "="*60)
    print("📋 快速启动命令:")
    print("   python run.py")
    print("="*60)

if __name__ == "__main__":
    main() 