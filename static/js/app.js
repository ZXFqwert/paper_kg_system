// 应用状态
const AppState = {
    currentPage: 'search',
    searchResults: [],
    currentPaper: null,
    searchParams: {
        query: '',
        page: 1,
        per_page: 10,
        sort_by: 'relevance'
    },
    config: {},
    papers: [],
    chatHistory: [],
    isSearching: false,
    taskPolling: new Map()
};

// DOM 元素
const Elements = {
    // 导航
    navItems: document.querySelectorAll('.nav-item'),
    pages: document.querySelectorAll('.page'),
    
    // 搜索页面
    searchInput: document.getElementById('search-input'),
    searchBtn: document.getElementById('search-btn'),
    sortBy: document.getElementById('sort-by'),
    perPage: document.getElementById('per-page'),
    searchResults: document.getElementById('search-results'),
    pagination: document.getElementById('pagination'),
    prevPage: document.getElementById('prev-page'),
    nextPage: document.getElementById('next-page'),
    pageInfo: document.getElementById('page-info'),
    
    // 知识图谱页面
    buildGraphBtn: document.getElementById('build-graph-btn'),
    papersList: document.getElementById('papers-list'),
    togglePanel: document.getElementById('toggle-panel'),
    papersPanel: document.getElementById('papers-panel'),
    chatInput: document.getElementById('chat-input'),
    sendBtn: document.getElementById('send-btn'),
    chatHistory: document.getElementById('chat-history'),
    queryModeRadios: document.querySelectorAll('input[name="query-mode"]'),
    
    // 设置页面
    apiBase: document.getElementById('api-base'),
    apiKey: document.getElementById('api-key'),
    extractModel: document.getElementById('extract-model'),
    qaModel: document.getElementById('qa-model'),
    temperature: document.getElementById('temperature'),
    deepMode: document.getElementById('deep-mode'),
    chunkSize: document.getElementById('chunk-size'),
    chunkOverlap: document.getElementById('chunk-overlap'),
    saveSettings: document.getElementById('save-settings'),
    resetSettings: document.getElementById('reset-settings'),
    testConnection: document.getElementById('test-connection'),
    
    // 模态框
    paperModal: document.getElementById('paper-modal'),
    paperDetails: document.getElementById('paper-details'),
    progressModal: document.getElementById('progress-modal'),
    progressTitle: document.getElementById('progress-title'),
    progressFill: document.getElementById('progress-fill'),
    progressMessage: document.getElementById('progress-message'),
    
    // 提示框
    toast: document.getElementById('toast'),
    toastMessage: document.getElementById('toast-message'),
    
    // 状态显示
    collectedCount: document.getElementById('collected-count'),
    entitiesCount: document.getElementById('entities-count')
};

// 工具函数
const Utils = {
    async request(url, options = {}) {
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json'
            }
        };
        
        const finalOptions = { ...defaultOptions, ...options };
        
        try {
            const response = await fetch(url, finalOptions);
            const data = await response.json();
            return data;
        } catch (error) {
            console.error('Request error:', error);
            throw error;
        }
    },
    
    showToast(message, type = 'info') {
        Elements.toastMessage.textContent = message;
        Elements.toast.className = `toast show ${type}`;
        
        setTimeout(() => {
            Elements.toast.classList.remove('show');
        }, 4000);
    },
    
    showModal(modalElement) {
        modalElement.classList.add('show');
    },
    
    hideModal(modalElement) {
        modalElement.classList.remove('show');
    },
    
    formatDate(dateString) {
        return new Date(dateString).toLocaleDateString('zh-CN');
    },
    
    truncateText(text, maxLength = 200) {
        if (text.length <= maxLength) return text;
        return text.slice(0, maxLength) + '...';
    }
};

// 页面路由
const Router = {
    navigate(pageName) {
        // 更新导航状态
        Elements.navItems.forEach(item => {
            item.classList.remove('active');
            if (item.dataset.page === pageName) {
                item.classList.add('active');
            }
        });
        
        // 显示对应页面
        Elements.pages.forEach(page => {
            page.style.display = 'none';
            if (page.id === `${pageName}-page`) {
                page.style.display = 'block';
            }
        });
        
        AppState.currentPage = pageName;
        
        // 页面特定初始化
        switch (pageName) {
            case 'graph':
                PaperManager.loadPapers();
                break;
            case 'settings':
                Settings.loadConfig();
                break;
        }
    }
};

// 搜索管理
const Search = {
    async performSearch() {
        if (AppState.isSearching) return;
        
        const query = Elements.searchInput.value.trim();
        if (!query) {
            Utils.showToast('请输入搜索关键词', 'warning');
            return;
        }
        
        AppState.isSearching = true;
        Elements.searchBtn.disabled = true;
        Elements.searchBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 搜索中...';
        
        try {
            AppState.searchParams.query = query;
            AppState.searchParams.sort_by = Elements.sortBy.value;
            const perPage = parseInt(Elements.perPage.value);
            
            const searchData = {
                query: query,
                start: (AppState.searchParams.page - 1) * perPage,
                max_results: perPage,
                sort_by: AppState.searchParams.sort_by
            };
            
            const response = await Utils.request('/api/search', {
                method: 'POST',
                body: JSON.stringify(searchData)
            });
            
            if (response.error) {
                Utils.showToast('搜索失败: ' + response.error, 'error');
            } else {
                AppState.searchResults = response.papers;
                this.renderResults(response);
                this.updatePagination(response);
            }
        } catch (error) {
            Utils.showToast('搜索请求失败', 'error');
        } finally {
            AppState.isSearching = false;
            Elements.searchBtn.disabled = false;
            Elements.searchBtn.innerHTML = '<i class="fas fa-search"></i> 搜索';
        }
    },
    
    renderResults(response) {
        if (!response.papers || response.papers.length === 0) {
            Elements.searchResults.innerHTML = `
                <div class="no-results">
                    <i class="fas fa-search"></i>
                    <p>未找到相关论文</p>
                </div>
            `;
            return;
        }
        
        const papersHTML = response.papers.map(paper => this.createPaperCard(paper)).join('');
        Elements.searchResults.innerHTML = `<div class="papers-grid">${papersHTML}</div>`;
    },
    
    createPaperCard(paper) {
        const authors = paper.authors.slice(0, 3).join(', ') + (paper.authors.length > 3 ? ' 等' : '');
        const categories = paper.categories.slice(0, 3).map(cat => 
            `<span class="category-tag">${cat}</span>`
        ).join('');
        
        return `
            <div class="paper-card ${paper.is_collected ? 'collected' : ''}" data-paper-id="${paper.id}">
                <div class="paper-title" onclick="PaperDetails.show('${paper.id}')">${paper.title}</div>
                <div class="paper-authors">${authors}</div>
                <div class="paper-meta">
                    <span>发布时间: ${Utils.formatDate(paper.published)}</span>
                    <span>ID: ${paper.id}</span>
                </div>
                <div class="paper-categories">${categories}</div>
                <div class="paper-actions">
                    ${paper.is_collected ? 
                        '<button class="btn btn-outline btn-sm" disabled><i class="fas fa-check"></i> 已收录</button>' :
                        `<button class="btn btn-success btn-sm" onclick="Search.collectPaper('${paper.id}')"><i class="fas fa-plus"></i> 收录</button>`
                    }
                    <button class="btn btn-outline btn-sm" onclick="window.open('${paper.arxiv_url}', '_blank')">
                        <i class="fas fa-external-link-alt"></i> 查看原文
                    </button>
                    <button class="btn btn-outline btn-sm" onclick="window.open('${paper.pdf_url}', '_blank')">
                        <i class="fas fa-download"></i> 下载PDF
                    </button>
                </div>
            </div>
        `;
    },
    
    async collectPaper(paperId) {
        const paper = AppState.searchResults.find(p => p.id === paperId);
        if (!paper) return;
        
        try {
            const response = await Utils.request('/api/collect_paper', {
                method: 'POST',
                body: JSON.stringify({
                    paper_data: paper
                })
            });
            
            if (response.error) {
                Utils.showToast('收录失败: ' + response.error, 'error');
            } else {
                Utils.showToast(response.message || '论文收录成功', 'success');
                paper.is_collected = true;
                
                // 更新卡片显示
                const cardElement = document.querySelector(`[data-paper-id="${paperId}"]`);
                if (cardElement) {
                    cardElement.classList.add('collected');
                    const actionButton = cardElement.querySelector('.btn-success');
                    if (actionButton) {
                        actionButton.outerHTML = '<button class="btn btn-outline btn-sm" disabled><i class="fas fa-check"></i> 已收录</button>';
                    }
                }
                
                // 更新状态计数
                SystemStatus.updateStatus();
            }
        } catch (error) {
            Utils.showToast('收录请求失败', 'error');
        }
    },
    
    updatePagination(response) {
        const totalPages = Math.ceil(response.total / response.per_page);
        const currentPage = response.page;
        
        Elements.pageInfo.textContent = `第 ${currentPage} 页，共 ${totalPages} 页`;
        Elements.prevPage.disabled = currentPage <= 1;
        Elements.nextPage.disabled = currentPage >= totalPages;
        
        Elements.pagination.style.display = totalPages > 1 ? 'flex' : 'none';
    },
    
    changePage(direction) {
        if (direction === 'prev' && AppState.searchParams.page > 1) {
            AppState.searchParams.page--;
        } else if (direction === 'next') {
            AppState.searchParams.page++;
        }
        
        this.performSearch();
    }
};

// 论文详情
const PaperDetails = {
    show(paperId) {
        const paper = AppState.searchResults.find(p => p.id === paperId);
        if (!paper) return;
        
        const detailsHTML = `
            <h4>${paper.title}</h4>
            <p><strong>作者:</strong> ${paper.authors.join(', ')}</p>
            <p><strong>发布时间:</strong> ${Utils.formatDate(paper.published)}</p>
            <p><strong>分类:</strong> ${paper.categories.join(', ')}</p>
            <p><strong>摘要:</strong></p>
            <div style="max-height: 300px; overflow-y: auto; border: 1px solid #ddd; padding: 15px; border-radius: 5px; background: #f9f9f9;">
                ${paper.abstract}
            </div>
            <div style="margin-top: 20px;">
                <a href="${paper.arxiv_url}" target="_blank" class="btn btn-outline">查看原文</a>
                <a href="${paper.pdf_url}" target="_blank" class="btn btn-outline">下载PDF</a>
            </div>
        `;
        
        Elements.paperDetails.innerHTML = detailsHTML;
        Utils.showModal(Elements.paperModal);
    }
};

// 论文管理
const PaperManager = {
    async loadPapers() {
        try {
            const response = await Utils.request('/api/collected_papers');
            if (response.error) {
                Utils.showToast('加载收录论文失败: ' + response.error, 'error');
            } else {
                AppState.papers = Array.isArray(response) ? response : [];
                this.renderPapers();
            }
        } catch (error) {
            Utils.showToast('加载收录论文失败', 'error');
        }
    },
    
    renderPapers() {
        if (AppState.papers.length === 0) {
            Elements.papersList.innerHTML = `
                <div class="loading-placeholder">
                    <i class="fas fa-file-alt"></i>
                    <p>暂无收录论文</p>
                </div>
            `;
            return;
        }
        
        const papersHTML = AppState.papers.map(paper => this.createPaperItem(paper)).join('');
        Elements.papersList.innerHTML = papersHTML;
    },
    
    createPaperItem(paper) {
        const statusClass = paper.extracted ? 'extracted' : 
                           paper.extraction_status === 'running' ? 'extracting' : '';
        
        const actionButton = paper.extracted ? 
            '<button class="btn btn-outline btn-sm" disabled><i class="fas fa-check"></i> 已抽取</button>' :
            paper.extraction_status === 'running' ?
            '<button class="btn btn-outline btn-sm" disabled><i class="fas fa-spinner fa-spin"></i> 抽取中</button>' :
            `<button class="btn btn-primary btn-sm" onclick="PaperManager.extractPaper('${paper.id}')"><i class="fas fa-cogs"></i> 抽取</button>`;
        
        return `
            <div class="paper-item ${statusClass}" data-paper-id="${paper.id}">
                <div class="paper-item-title">${Utils.truncateText(paper.title, 80)}</div>
                <div class="paper-item-meta">
                    收录时间: ${Utils.formatDate(paper.collected_at)} | 
                    状态: ${this.getStatusText(paper)}
                </div>
                <div class="paper-item-actions">
                    ${actionButton}
                </div>
            </div>
        `;
    },
    
    getStatusText(paper) {
        switch (paper.extraction_status) {
            case 'completed': return '已完成';
            case 'running': return '抽取中';
            case 'failed': return '失败';
            default: return '待抽取';
        }
    },
    
    async extractPaper(paperId) {
        try {
            const response = await Utils.request(`/api/extract_paper/${paperId}`, {
                method: 'POST'
            });
            
            if (response.error) {
                Utils.showToast('启动抽取失败: ' + response.error, 'error');
            } else if (response.task_id) {
                Utils.showToast(response.message || '开始抽取论文...', 'info');
                this.startTaskPolling(response.task_id, paperId, 'extract');
                
                // 更新按钮状态
                const paperItem = document.querySelector(`[data-paper-id="${paperId}"]`);
                if (paperItem) {
                    paperItem.classList.add('extracting');
                    const button = paperItem.querySelector('.btn');
                    button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 抽取中';
                    button.disabled = true;
                }
            } else {
                Utils.showToast('启动抽取失败: 未知错误', 'error');
            }
        } catch (error) {
            Utils.showToast('抽取请求失败', 'error');
        }
    },
    
    async buildGraph() {
        try {
            const response = await Utils.request('/api/build_graph', {
                method: 'POST'
            });
            
            if (response.error) {
                Utils.showToast('启动构建失败: ' + response.error, 'error');
            } else if (response.task_id) {
                Utils.showToast(response.message || '开始构建知识图谱...', 'info');
                Elements.progressTitle.textContent = '构建知识图谱';
                Utils.showModal(Elements.progressModal);
                this.startTaskPolling(response.task_id, null, 'build');
            } else {
                Utils.showToast('启动构建失败: 未知错误', 'error');
            }
        } catch (error) {
            Utils.showToast('构建请求失败', 'error');
        }
    },
    
    startTaskPolling(taskId, paperId, taskType) {
        const pollInterval = setInterval(async () => {
            try {
                const response = await Utils.request(`/api/task_status/${taskId}`);
                
                if (taskType === 'build') {
                    // 更新进度模态框
                    Elements.progressFill.style.width = `${response.progress}%`;
                    Elements.progressMessage.textContent = response.message;
                }
                
                if (response.status === 'completed') {
                    clearInterval(pollInterval);
                    AppState.taskPolling.delete(taskId);
                    
                    if (taskType === 'extract') {
                        Utils.showToast('论文抽取完成', 'success');
                        this.loadPapers(); // 重新加载论文列表
                    } else if (taskType === 'build') {
                        Utils.hideModal(Elements.progressModal);
                        Utils.showToast('知识图谱构建完成', 'success');
                    }
                    
                    SystemStatus.updateStatus();
                } else if (response.status === 'failed') {
                    clearInterval(pollInterval);
                    AppState.taskPolling.delete(taskId);
                    
                    if (taskType === 'build') {
                        Utils.hideModal(Elements.progressModal);
                    }
                    
                    Utils.showToast(`任务失败: ${response.message}`, 'error');
                    this.loadPapers(); // 重新加载以更新状态
                }
            } catch (error) {
                console.error('轮询任务状态失败:', error);
            }
        }, 2000);
        
        AppState.taskPolling.set(taskId, pollInterval);
    },
    
    togglePanel() {
        Elements.papersPanel.classList.toggle('collapsed');
        const icon = Elements.togglePanel.querySelector('i');
        if (Elements.papersPanel.classList.contains('collapsed')) {
            icon.className = 'fas fa-chevron-right';
        } else {
            icon.className = 'fas fa-chevron-left';
        }
    }
};

// 聊天系统
const Chat = {
    async sendMessage() {
        const query = Elements.chatInput.value.trim();
        if (!query) return;
        
        // 添加用户消息
        this.addMessage(query, 'user');
        Elements.chatInput.value = '';
        Elements.sendBtn.disabled = true;
        
        // 获取查询模式
        const mode = document.querySelector('input[name="query-mode"]:checked').value;
        
        try {
            const response = await Utils.request('/api/query', {
                method: 'POST',
                body: JSON.stringify({ question: query, mode })
            });
            
            if (response.error) {
                this.addMessage(`抱歉，查询失败：${response.error}`, 'assistant');
            } else if (response.answer) {
                this.addMessage(response.answer, 'assistant');
            } else {
                this.addMessage('抱歉，查询失败：未知错误', 'assistant');
            }
        } catch (error) {
            this.addMessage('抱歉，网络请求失败，请稍后重试。', 'assistant');
        } finally {
            Elements.sendBtn.disabled = false;
        }
    },
    
    addMessage(content, type) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-message ${type}`;
        messageDiv.textContent = content;
        
        // 移除欢迎消息
        const welcomeMessage = Elements.chatHistory.querySelector('.welcome-message');
        if (welcomeMessage) {
            welcomeMessage.remove();
        }
        
        Elements.chatHistory.appendChild(messageDiv);
        Elements.chatHistory.scrollTop = Elements.chatHistory.scrollHeight;
        
        AppState.chatHistory.push({ content, type });
    }
};

// 设置管理
const Settings = {
    async loadConfig() {
        try {
            const response = await Utils.request('/api/config');
            if (response.error) {
                Utils.showToast('加载配置失败: ' + response.error, 'error');
            } else {
                AppState.config = response;
                this.populateForm();
            }
        } catch (error) {
            Utils.showToast('加载配置失败', 'error');
        }
    },
    
    populateForm() {
        const config = AppState.config;
        
        // OpenAI设置
        Elements.apiBase.value = config.openai?.api_base || '';
        
        // 处理API Key显示
        const apiKey = config.openai?.api_key || '';
        Elements.apiKey.value = apiKey;
        
        // 记录原始API Key（用于判断是否被修改）
        AppState.originalApiKey = apiKey;
        
        // 如果是掩码格式，添加提示
        if (apiKey && apiKey.includes('*')) {
            Elements.apiKey.placeholder = '已保存API Key（显示为掩码）';
            Elements.apiKey.title = '已保存API Key，显示为掩码格式。如需修改请重新输入完整的API Key。';
        } else {
            Elements.apiKey.placeholder = '请输入OpenAI API Key';
            Elements.apiKey.title = '';
        }
        
        Elements.extractModel.value = config.openai?.extract_model || 'gpt-4o-mini';
        Elements.qaModel.value = config.openai?.qa_model || 'gpt-4o';
        Elements.temperature.value = config.openai?.temperature || 0.1;
        
        // 系统设置
        Elements.deepMode.checked = config.system?.deep_mode || false;
        Elements.chunkSize.value = config.system?.chunk_size || 1200;
        Elements.chunkOverlap.value = config.system?.chunk_overlap || 100;
    },
    
    async saveConfig() {
        const config = {
            openai: {
                api_base: Elements.apiBase.value,
                extract_model: Elements.extractModel.value,
                qa_model: Elements.qaModel.value,
                temperature: parseFloat(Elements.temperature.value)
            },
            system: {
                deep_mode: Elements.deepMode.checked,
                chunk_size: parseInt(Elements.chunkSize.value),
                chunk_overlap: parseInt(Elements.chunkOverlap.value)
            }
        };
        
        // 检查API Key是否被修改
        const currentApiKey = Elements.apiKey.value;
        const isMasked = currentApiKey.includes('*');
        const isChanged = currentApiKey !== AppState.originalApiKey;
        
        // 只有当API Key不是掩码格式或者被修改时才发送
        if (!isMasked || isChanged) {
            config.openai.api_key = currentApiKey;
        }
        
        try {
            const response = await Utils.request('/api/config', {
                method: 'POST',
                body: JSON.stringify(config)
            });
            
            if (response.error) {
                Utils.showToast('保存失败: ' + response.error, 'error');
                return false;
            } else {
                AppState.config = config;
                Utils.showToast(response.message || '设置保存成功', 'success');
                return true;
            }
        } catch (error) {
            Utils.showToast('保存请求失败', 'error');
            return false;
        }
    },
    
    resetConfig() {
        if (confirm('确定要重置所有设置吗？')) {
            this.populateForm(); // 重新加载原始配置
            Utils.showToast('设置已重置', 'info');
        }
    },
    
    async testConnection() {
        Elements.testConnection.disabled = true;
        Elements.testConnection.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 测试中...';
        
        try {
            // 先保存当前配置
            const saveSuccess = await this.saveConfig();
            if (!saveSuccess) {
                return; // 保存失败则不继续测试
            }
            
            // 测试连接 - 直接使用后端已保存的配置
            const testData = {
                use_saved_config: true
            };
            
            const response = await Utils.request('/api/test_openai', {
                method: 'POST',
                body: JSON.stringify(testData)
            });
            
            if (response.error) {
                Utils.showToast('连接测试失败: ' + response.error, 'error');
            } else {
                Utils.showToast(response.message || '连接测试成功', 'success');
            }
        } catch (error) {
            Utils.showToast('连接测试失败', 'error');
        } finally {
            Elements.testConnection.disabled = false;
            Elements.testConnection.innerHTML = '<i class="fas fa-plug"></i> 测试连接';
        }
    }
};

// 系统状态
const SystemStatus = {
    async updateStatus() {
        try {
            const response = await Utils.request('/api/system_status');
            if (response.success) {
                const status = response.status;
                Elements.collectedCount.textContent = status.collected_papers;
                Elements.entitiesCount.textContent = status.entities_count;
            }
        } catch (error) {
            console.error('更新系统状态失败:', error);
        }
    }
};

// 事件监听器
const Events = {
    init() {
        // 导航事件
        Elements.navItems.forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                Router.navigate(item.dataset.page);
            });
        });
        
        // 搜索事件
        Elements.searchBtn.addEventListener('click', () => Search.performSearch());
        Elements.searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') Search.performSearch();
        });
        Elements.sortBy.addEventListener('change', () => {
            if (AppState.searchParams.query) {
                AppState.searchParams.page = 1;
                Search.performSearch();
            }
        });
        Elements.perPage.addEventListener('change', () => {
            if (AppState.searchParams.query) {
                AppState.searchParams.page = 1;
                Search.performSearch();
            }
        });
        
        // 分页事件
        Elements.prevPage.addEventListener('click', () => Search.changePage('prev'));
        Elements.nextPage.addEventListener('click', () => Search.changePage('next'));
        
        // 知识图谱事件
        Elements.buildGraphBtn.addEventListener('click', () => PaperManager.buildGraph());
        Elements.togglePanel.addEventListener('click', () => PaperManager.togglePanel());
        Elements.sendBtn.addEventListener('click', () => Chat.sendMessage());
        Elements.chatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') Chat.sendMessage();
        });
        
        // 设置事件
        Elements.saveSettings.addEventListener('click', () => Settings.saveConfig());
        Elements.resetSettings.addEventListener('click', () => Settings.resetConfig());
        Elements.testConnection.addEventListener('click', () => Settings.testConnection());
        
        // 模态框事件
        document.querySelectorAll('.modal-close').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const modal = e.target.closest('.modal');
                Utils.hideModal(modal);
            });
        });
        
        // 点击模态框背景关闭
        document.querySelectorAll('.modal').forEach(modal => {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    Utils.hideModal(modal);
                }
            });
        });
        
        // 提示框关闭
        document.querySelector('.toast-close').addEventListener('click', () => {
            Elements.toast.classList.remove('show');
        });
    }
};

// 应用初始化
const App = {
    init() {
        Events.init();
        SystemStatus.updateStatus();
        Router.navigate('search'); // 默认显示搜索页面
        
        // 定期更新系统状态
        setInterval(() => {
            SystemStatus.updateStatus();
        }, 30000); // 30秒更新一次
    }
};

// 启动应用
document.addEventListener('DOMContentLoaded', () => {
    App.init();
}); 