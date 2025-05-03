/**
 * Main JavaScript for the 智能文献处理系统
 */

// Initialize API client
const api = new ApiClient();

// DOM elements
const searchForm = document.getElementById('searchForm');
const searchResults = document.getElementById('searchResults');
const compareSelectedBtn = document.getElementById('compareSelected');
const generateSynthesisBtn = document.getElementById('generateSynthesis');
const generateFromUploadedBtn = document.getElementById('generateFromUploaded');
const processingIndicator = document.getElementById('processingIndicator');
const synthesisResult = document.getElementById('synthesisResult');
const fileDropzone = document.getElementById('fileDropzone');
const fileInput = document.getElementById('fileInput');

// Global variables
let selectedPapers = [];
let searchResultPapers = [];
let uploadedFiles = [];
let currentTask = null;

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
    setupEventListeners();
});

/**
 * Initialize the application
 */
function initializeApp() {
    // Check API health
    api.checkHealth()
        .then(response => {
            console.log('API health check:', response);
        })
        .catch(error => {
            console.error('API health check failed:', error);
            showAlert('API连接失败，请检查服务器是否运行', 'danger');
        });
    
    // Check configuration
    api.getConfigInfo()
        .then(config => {
            console.log('API configuration:', config);
            
            // Show warnings if API keys are missing
            if (!config.google_key_available) {
                showAlert('Google搜索API密钥未配置，搜索功能可能受限', 'warning');
            }
            
            if (!config.openai_api_available) {
                showAlert('OpenAI API密钥未配置，综述生成功能可能受限', 'warning');
            }
            
            if (!config.mineru_api_available) {
                showAlert('MinerU API密钥未配置，PDF处理功能可能受限', 'warning');
            }
        })
        .catch(error => {
            console.error('Failed to get configuration:', error);
        });
}

/**
 * Set up event listeners
 */
function setupEventListeners() {
    // Search form submission
    if (searchForm) {
        searchForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const query = searchForm.querySelector('input[type="text"]').value;
            if (query.trim()) {
                performSearch(query);
            }
        });
    }
    
    // Compare selected papers button
    if (compareSelectedBtn) {
        compareSelectedBtn.addEventListener('click', function() {
            if (selectedPapers.length > 0) {
                document.getElementById('synthesis').scrollIntoView({behavior: 'smooth'});
                document.querySelector('#synthesisTabs .nav-link[href="#selectedPapers"]').click();
                updateSelectedPapersList();
            } else {
                showAlert('请先选择要对比的论文', 'warning');
            }
        });
    }
    
    // Generate synthesis button (from selected papers)
    if (generateSynthesisBtn) {
        generateSynthesisBtn.addEventListener('click', function() {
            if (selectedPapers.length > 0) {
                generateSynthesis(selectedPapers);
            } else {
                showAlert('请先选择要对比的论文', 'warning');
            }
        });
    }
    
    // Generate synthesis button (from uploaded files)
    if (generateFromUploadedBtn) {
        generateFromUploadedBtn.addEventListener('click', function() {
            if (uploadedFiles.length > 0) {
                generateSynthesisFromUploads(uploadedFiles);
            } else {
                showAlert('请先上传PDF文件', 'warning');
            }
        });
    }
    
    // File dropzone
    if (fileDropzone) {
        fileDropzone.addEventListener('dragover', function(e) {
            e.preventDefault();
            fileDropzone.classList.add('border-primary');
        });
        
        fileDropzone.addEventListener('dragleave', function() {
            fileDropzone.classList.remove('border-primary');
        });
        
        fileDropzone.addEventListener('drop', function(e) {
            e.preventDefault();
            fileDropzone.classList.remove('border-primary');
            
            if (e.dataTransfer.files.length > 0) {
                handleFileUpload(e.dataTransfer.files);
            }
        });
        
        fileDropzone.addEventListener('click', function() {
            fileInput.click();
        });
    }
    
    // File input change
    if (fileInput) {
        fileInput.addEventListener('change', function() {
            if (fileInput.files.length > 0) {
                handleFileUpload(fileInput.files);
            }
        });
    }
    
    // Paper selection in search results
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('form-check-input') && e.target.closest('.paper-item')) {
            const paperId = e.target.id;
            const paperIndex = parseInt(paperId.replace('paper', '')) - 1;
            
            if (e.target.checked) {
                if (selectedPapers.length >= 5) {
                    e.target.checked = false;
                    showAlert('最多只能选择5篇论文进行对比', 'warning');
                } else if (searchResultPapers[paperIndex]) {
                    selectedPapers.push(searchResultPapers[paperIndex]);
                }
            } else {
                selectedPapers = selectedPapers.filter(p => p.arxiv_id !== searchResultPapers[paperIndex].arxiv_id);
            }
            
            updateSelectedCount();
        }
    });
    
    // Remove selected paper
    document.addEventListener('click', function(e) {
        if (e.target.closest('.btn-outline-danger') && e.target.closest('.list-group-item')) {
            const listItem = e.target.closest('.list-group-item');
            const index = Array.from(listItem.parentNode.children).indexOf(listItem);
            
            if (index !== -1 && index < selectedPapers.length) {
                selectedPapers.splice(index, 1);
                updateSelectedPapersList();
                updateSelectedCount();
            }
        }
    });
    
    // Remove uploaded file
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('remove-file')) {
            const fileItem = e.target.closest('.file-item');
            const index = Array.from(fileItem.parentNode.children).indexOf(fileItem);
            
            if (index !== -1 && index < uploadedFiles.length) {
                uploadedFiles.splice(index, 1);
                updateUploadedFilesList();
            }
        }
    });
    
    // Expand citations button
    document.addEventListener('click', function(e) {
        if (e.target.closest('.expand-citations')) {
            const button = e.target.closest('.expand-citations');
            const arxivId = button.getAttribute('data-arxiv-id');
            
            if (arxivId) {
                expandCitations(arxivId, button);
            }
        }
    });
    
    // Smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            
            document.querySelector(this.getAttribute('href')).scrollIntoView({
                behavior: 'smooth'
            });
        });
    });
}

/**
 * Perform a search for papers
 * @param {string} query - Search query
 */
function performSearch(query) {
    // Show loading state
    searchResults.innerHTML = `
        <div class="text-center my-5">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            <p class="mt-3">正在搜索论文，这可能需要一些时间...</p>
        </div>
    `;
    
    // Reset selected papers
    selectedPapers = [];
    searchResultPapers = [];
    updateSelectedCount();
    
    // Perform search
    api.searchPapers(query, {
        searchQueries: 5,
        searchPapers: 10,
        expandPapers: 10
    })
    .then(response => {
        console.log('Search task started:', response);
        currentTask = {
            id: response.task_id,
            type: 'search'
        };
        
        // Poll for task completion
        return pollTaskStatus(response.task_id, 'search');
    })
    .then(result => {
        console.log('Search completed:', result);
        
        // Process search results
        if (result.result && result.result.papers) {
            searchResultPapers = result.result.papers;
            displaySearchResults(result.result.papers, result.result.total_found);
        } else {
            searchResults.innerHTML = `
                <div class="alert alert-info">
                    <i class="fas fa-info-circle me-2"></i>
                    未找到相关论文
                </div>
            `;
        }
    })
    .catch(error => {
        console.error('Search failed:', error);
        searchResults.innerHTML = `
            <div class="alert alert-danger">
                <i class="fas fa-exclamation-circle me-2"></i>
                搜索失败: ${error.message}
            </div>
        `;
    });
}

/**
 * Display search results
 * @param {Array} papers - List of papers
 * @param {number} totalFound - Total number of papers found
 */
function displaySearchResults(papers, totalFound) {
    if (!papers || papers.length === 0) {
        searchResults.innerHTML = `
            <div class="alert alert-info">
                <i class="fas fa-info-circle me-2"></i>
                未找到相关论文
            </div>
        `;
        return;
    }
    
    // Create header
    let html = `
        <div class="d-flex justify-content-between align-items-center mb-3">
            <h5>搜索结果 <span class="badge bg-secondary">${totalFound}篇</span></h5>
            <div>
                <button id="compareSelected" class="btn btn-accent">
                    <i class="fas fa-file-contract me-1"></i> 对比选中文献 (<span class="selected-count">0</span>)
                </button>
            </div>
        </div>
        
        <div class="paper-list">
    `;
    
    // Create paper items
    papers.forEach((paper, index) => {
        const score = paper.score ? (paper.score * 100).toFixed(0) : '';
        const scoreClass = score > 80 ? 'text-success' : (score > 60 ? 'text-warning' : 'text-danger');
        
        html += `
            <div class="paper-item">
                <div class="form-check">
                    <input class="form-check-input" type="checkbox" id="paper${index + 1}">
                    <label class="form-check-label" for="paper${index + 1}">
                        <div class="paper-title">${paper.title}</div>
                        <div class="paper-authors">${paper.authors ? paper.authors.join(', ') : ''}</div>
                        <div class="paper-abstract">
                            ${paper.abstract ? paper.abstract.substring(0, 300) + '...' : ''}
                        </div>
                        <div class="paper-meta">
                            <span class="paper-journal">${paper.source || ''}</span>
                            <span class="paper-year">${paper.published || ''}</span>
                            ${score ? `<span class="paper-citation ${scoreClass}">相关度: ${score}%</span>` : ''}
                        </div>
                        <div class="mt-2 d-flex justify-content-between align-items-center">
                            <div>
                                <span class="tag">arXiv:${paper.arxiv_id}</span>
                                ${paper.depth ? `<span class="tag">引用深度: ${paper.depth}</span>` : ''}
                            </div>
                            <button class="btn btn-sm btn-outline-primary expand-citations" data-arxiv-id="${paper.arxiv_id}">
                                <i class="fas fa-project-diagram me-1"></i> 扩展引文
                            </button>
                        </div>
                    </label>
                </div>
            </div>
        `;
    });
    
    // Close paper list and add pagination
    html += `
        </div>
        
        <nav aria-label="Page navigation" class="mt-4">
            <ul class="pagination justify-content-center">
                <li class="page-item disabled">
                    <a class="page-link" href="#" tabindex="-1">上一页</a>
                </li>
                <li class="page-item active"><a class="page-link" href="#">1</a></li>
                <li class="page-item disabled"><a class="page-link" href="#">2</a></li>
                <li class="page-item disabled"><a class="page-link" href="#">3</a></li>
                <li class="page-item disabled">
                    <a class="page-link" href="#">下一页</a>
                </li>
            </ul>
        </nav>
    `;
    
    // Update search results
    searchResults.innerHTML = html;
    
    // Update compare selected button
    const compareSelectedBtn = document.getElementById('compareSelected');
    if (compareSelectedBtn) {
        compareSelectedBtn.addEventListener('click', function() {
            if (selectedPapers.length > 0) {
                document.getElementById('synthesis').scrollIntoView({behavior: 'smooth'});
                document.querySelector('#synthesisTabs .nav-link[href="#selectedPapers"]').click();
                updateSelectedPapersList();
            } else {
                showAlert('请先选择要对比的论文', 'warning');
            }
        });
    }
}

/**
 * Update the selected papers count
 */
function updateSelectedCount() {
    const selectedCountElements = document.querySelectorAll('.selected-count');
    selectedCountElements.forEach(element => {
        element.textContent = selectedPapers.length;
    });
}

/**
 * Update the selected papers list
 */
function updateSelectedPapersList() {
    const selectedPapersList = document.querySelector('.selected-papers');
    if (!selectedPapersList) return;
    
    if (selectedPapers.length === 0) {
        selectedPapersList.innerHTML = `
            <li class="list-group-item text-center text-muted">
                未选择任何论文
            </li>
        `;
        return;
    }
    
    let html = '';
    selectedPapers.forEach(paper => {
        html += `
            <li class="list-group-item d-flex justify-content-between align-items-center">
                <div>
                    <div class="fw-bold">${paper.title}</div>
                    <small class="text-muted">arXiv:${paper.arxiv_id}</small>
                </div>
                <button class="btn btn-sm btn-outline-danger">
                    <i class="fas fa-times"></i>
                </button>
            </li>
        `;
    });
    
    selectedPapersList.innerHTML = html;
}

/**
 * Handle file upload
 * @param {FileList} files - Uploaded files
 */
function handleFileUpload(files) {
    const validFiles = Array.from(files).filter(file => file.type === 'application/pdf');
    
    if (validFiles.length === 0) {
        showAlert('请上传PDF格式的文件', 'warning');
        return;
    }
    
    if (uploadedFiles.length + validFiles.length > 5) {
        showAlert('最多只能上传5个PDF文件', 'warning');
        return;
    }
    
    // Add valid files to the list
    uploadedFiles = [...uploadedFiles, ...validFiles];
    
    // Update the UI
    updateUploadedFilesList();
    
    // Reset file input
    if (fileInput) {
        fileInput.value = '';
    }
}

/**
 * Update the uploaded files list
 */
function updateUploadedFilesList() {
    const uploadedFilesList = document.querySelector('.uploaded-files');
    if (!uploadedFilesList) return;
    
    let html = `<h5 class="mt-4 mb-3">已上传文件（${uploadedFiles.length}）</h5>`;
    
    if (uploadedFiles.length === 0) {
        html += `
            <div class="text-center text-muted">
                未上传任何文件
            </div>
        `;
    } else {
        uploadedFiles.forEach(file => {
            html += `
                <div class="file-item">
                    <div class="file-name">${file.name}</div>
                    <i class="fas fa-times-circle remove-file"></i>
                </div>
            `;
        });
    }
    
    uploadedFilesList.innerHTML = html;
}

/**
 * Generate synthesis from selected papers
 * @param {Array} papers - Selected papers
 */
function generateSynthesis(papers) {
    if (papers.length === 0) {
        showAlert('请先选择要对比的论文', 'warning');
        return;
    }
    
    if (papers.length > 5) {
        showAlert('最多只能选择5篇论文进行对比', 'warning');
        return;
    }
    
    // Show processing indicator
    processingIndicator.style.display = 'block';
    synthesisResult.style.display = 'none';
    
    // Get options
    const options = {
        includeMethodology: document.getElementById('includeMethodology')?.checked ?? true,
        includeResults: document.getElementById('includeResults')?.checked ?? true,
        includeGaps: document.getElementById('includeGaps')?.checked ?? false
    };
    
    // Extract arXiv IDs
    const arxivIds = papers.map(paper => paper.arxiv_id);
    
    // Generate review
    api.generateReviewFromArxiv(arxivIds, options)
        .then(response => {
            console.log('Review task started:', response);
            currentTask = {
                id: response.task_id,
                type: 'review'
            };
            
            // Poll for task completion
            return pollTaskStatus(response.task_id, 'review');
        })
        .then(result => {
            console.log('Review completed:', result);
            
            // Display review
            if (result.result && result.result.review) {
                displayReview(result.result.review, papers);
            } else {
                throw new Error('未能生成综述');
            }
        })
        .catch(error => {
            console.error('Review generation failed:', error);
            processingIndicator.style.display = 'none';
            showAlert(`综述生成失败: ${error.message}`, 'danger');
        });
}

/**
 * Generate synthesis from uploaded files
 * @param {Array} files - Uploaded files
 */
function generateSynthesisFromUploads(files) {
    if (files.length === 0) {
        showAlert('请先上传PDF文件', 'warning');
        return;
    }
    
    if (files.length > 5) {
        showAlert('最多只能上传5个PDF文件', 'warning');
        return;
    }
    
    // Show processing indicator
    processingIndicator.style.display = 'block';
    synthesisResult.style.display = 'none';
    
    // Get options
    const options = {
        extractMetadata: document.getElementById('extractMetadata')?.checked ?? true,
        detailedAnalysis: document.getElementById('detailedAnalysis')?.checked ?? false
    };
    
    // Create form data
    const formData = new FormData();
    files.forEach(file => {
        formData.append('files', file);
    });
    formData.append('options', JSON.stringify(options));
    
    // Upload files and generate review
    api.uploadFiles('/api/review/files', formData)
        .then(response => {
            console.log('Upload task started:', response);
            currentTask = {
                id: response.task_id,
                type: 'review'
            };
            
            // Poll for task completion
            return pollTaskStatus(response.task_id, 'review');
        })
        .then(result => {
            console.log('Review completed:', result);
            
            // Display review
            if (result.result && result.result.review) {
                displayReview(result.result.review, files.map(f => ({ title: f.name })));
            } else {
                throw new Error('未能生成综述');
            }
        })
        .catch(error => {
            console.error('Review generation failed:', error);
            processingIndicator.style.display = 'none';
            showAlert(`综述生成失败: ${error.message}`, 'danger');
        });
}

/**
 * Display the generated review
 * @param {string} review - Generated review
 * @param {Array} papers - Papers used for the review
 */
function displayReview(review, papers) {
    // Hide processing indicator
    processingIndicator.style.display = 'none';
    
    // Format the review (convert markdown to HTML)
    const formattedReview = formatReview(review);
    
    // Create review title
    let title = '多文献对比综述';
    if (papers.length > 0) {
        if (papers.length === 1) {
            title = `《${papers[0].title}》的综述分析`;
        } else {
            title = `${papers.length}篇文献的对比综述`;
        }
    }
    
    // Update the review container
    synthesisResult.querySelector('.card-body').innerHTML = `
        <h4>${title}</h4>
        <div class="review-content">
            ${formattedReview}
        </div>
    `;
    
    // Show the review
    synthesisResult.style.display = 'block';
    
    // Scroll to the review
    synthesisResult.scrollIntoView({behavior: 'smooth'});
}

/**
 * Format the review text (convert markdown to HTML)
 * @param {string} review - Review text
 * @returns {string} - Formatted HTML
 */
function formatReview(review) {
    // Simple markdown to HTML conversion
    let html = review
        // Headers
        .replace(/^# (.*$)/gm, '<h2>$1</h2>')
        .replace(/^## (.*$)/gm, '<h3>$1</h3>')
        .replace(/^### (.*$)/gm, '<h4>$1</h4>')
        .replace(/^#### (.*$)/gm, '<h5>$1</h5>')
        
        // Bold
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        
        // Italic
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        
        // Lists
        .replace(/^\s*\d+\.\s+(.*$)/gm, '<li>$1</li>')
        .replace(/^\s*\-\s+(.*$)/gm, '<li>$1</li>')
        
        // Paragraphs
        .replace(/\n\n/g, '</p><p>')
        
        // Line breaks
        .replace(/\n/g, '<br>');
    
    // Wrap in paragraph tags
    html = `<p>${html}</p>`;
    
    // Fix lists
    html = html.replace(/<li>(.*?)<\/li>/g, function(match) {
        if (html.indexOf('<ul>') === -1) {
            return '<ul>' + match + '</ul>';
        }
        return match;
    });
    
    return html;
}

/**
 * Poll for task status
 * @param {string} taskId - Task ID
 * @param {string} type - Task type ('search' or 'review')
 * @returns {Promise<Object>} - Task result
 */
function pollTaskStatus(taskId, type) {
    return new Promise((resolve, reject) => {
        const endpoint = type === 'review' ? '/api/review/task' : '/api/search/task';
        const maxPolls = 60; // 5 minutes (5s interval)
        const interval = 5000; // 5 seconds
        
        let pollCount = 0;
        
        // Update progress bar
        const progressBar = processingIndicator.querySelector('.progress-bar');
        if (progressBar) {
            progressBar.style.width = '0%';
        }
        
        const poll = () => {
            api.get(`${endpoint}/${taskId}`)
                .then(response => {
                    pollCount++;
                    
                    // Update progress bar
                    if (progressBar && response.progress) {
                        progressBar.style.width = `${response.progress * 100}%`;
                    }
                    
                    if (response.status === 'completed') {
                        resolve(response);
                    } else if (response.status === 'failed') {
                        reject(new Error(response.message || '任务失败'));
                    } else if (pollCount >= maxPolls) {
                        reject(new Error('任务超时'));
                    } else {
                        setTimeout(poll, interval);
                    }
                })
                .catch(error => {
                    reject(error);
                });
        };
        
        poll();
    });
}

/**
 * Expand citations for a paper
 * @param {string} arxivId - arXiv ID of the paper
 * @param {HTMLElement} button - Button element that was clicked
 */
function expandCitations(arxivId, button) {
    // Change button state
    const originalText = button.innerHTML;
    button.innerHTML = `
        <span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
        <span class="ms-1">扩展中...</span>
    `;
    button.disabled = true;
    
    // Call API to expand citations
    api.post('/api/search/expand', {
        arxiv_id: arxivId,
        depth: 1
    })
    .then(response => {
        console.log('Expand citations task started:', response);
        
        // Poll for task completion
        return pollTaskStatus(response.task_id, 'search');
    })
    .then(result => {
        console.log('Expand citations completed:', result);
        
        // Process results
        if (result.result && result.result.cited_papers) {
            const citedPapers = result.result.cited_papers;
            
            // Add cited papers to search results
            searchResultPapers = [...searchResultPapers, ...citedPapers];
            
            // Update UI
            const paperItem = button.closest('.paper-item');
            
            // Create cited papers section
            let citedHtml = `
                <div class="cited-papers mt-3 pt-3 border-top">
                    <h6 class="mb-3">引用文献 (${citedPapers.length})</h6>
            `;
            
            if (citedPapers.length === 0) {
                citedHtml += `
                    <div class="text-muted">未找到引用文献</div>
                `;
            } else {
                citedPapers.forEach((paper, idx) => {
                    const score = paper.score ? (paper.score * 100).toFixed(0) : '';
                    const scoreClass = score > 80 ? 'text-success' : (score > 60 ? 'text-warning' : 'text-danger');
                    
                    citedHtml += `
                        <div class="cited-paper-item mb-3 ps-3 border-start border-primary">
                            <div class="form-check">
                                <input class="form-check-input" type="checkbox" id="cited${searchResultPapers.length - citedPapers.length + idx}">
                                <label class="form-check-label" for="cited${searchResultPapers.length - citedPapers.length + idx}">
                                    <div class="paper-title">${paper.title}</div>
                                    <div class="paper-meta">
                                        <span class="paper-journal">${paper.source || ''}</span>
                                        <span class="tag">arXiv:${paper.arxiv_id}</span>
                                        <span class="tag">引用章节: ${paper.section}</span>
                                        ${score ? `<span class="paper-citation ${scoreClass}">相关度: ${score}%</span>` : ''}
                                    </div>
                                </label>
                            </div>
                        </div>
                    `;
                });
            }
            
            citedHtml += `</div>`;
            
            // Append cited papers to paper item
            paperItem.insertAdjacentHTML('beforeend', citedHtml);
            
            // Update button
            button.innerHTML = `
                <i class="fas fa-check me-1"></i> 已扩展 (${citedPapers.length})
            `;
            button.disabled = true;
            button.classList.remove('btn-outline-primary');
            button.classList.add('btn-success');
            
            // Show success message
            showAlert(`成功扩展引文，找到 ${citedPapers.length} 篇引用文献`, 'success');
        } else {
            throw new Error('未能获取引用文献');
        }
    })
    .catch(error => {
        console.error('Expand citations failed:', error);
        
        // Reset button
        button.innerHTML = originalText;
        button.disabled = false;
        
        // Show error message
        showAlert(`扩展引文失败: ${error.message}`, 'danger');
    });
}

/**
 * Show an alert message
 * @param {string} message - Alert message
 * @param {string} type - Alert type ('success', 'info', 'warning', 'danger')
 */
function showAlert(message, type = 'info') {
    const alertContainer = document.createElement('div');
    alertContainer.className = `alert alert-${type} alert-dismissible fade show`;
    alertContainer.setAttribute('role', 'alert');
    alertContainer.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    // Add to the top of the page
    document.body.insertBefore(alertContainer, document.body.firstChild);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        alertContainer.classList.remove('show');
        setTimeout(() => {
            alertContainer.remove();
        }, 150);
    }, 5000);
}
