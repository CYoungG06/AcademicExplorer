/**
 * API client for the 智能文献处理系统
 */
class ApiClient {
    constructor(baseUrl = '') {
        this.baseUrl = baseUrl || window.location.origin;
    }

    /**
     * Make a GET request to the API
     * @param {string} endpoint - API endpoint
     * @param {Object} params - Query parameters
     * @returns {Promise<Object>} - Response data
     */
    async get(endpoint, params = {}) {
        const url = new URL(`${this.baseUrl}${endpoint}`);
        Object.keys(params).forEach(key => url.searchParams.append(key, params[key]));
        
        try {
            const response = await fetch(url.toString());
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error('GET request failed:', error);
            throw error;
        }
    }

    /**
     * Make a POST request to the API
     * @param {string} endpoint - API endpoint
     * @param {Object} data - Request body
     * @returns {Promise<Object>} - Response data
     */
    async post(endpoint, data = {}) {
        try {
            const response = await fetch(`${this.baseUrl}${endpoint}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data),
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('POST request failed:', error);
            throw error;
        }
    }

    /**
     * Upload files to the API
     * @param {string} endpoint - API endpoint
     * @param {FormData} formData - Form data with files
     * @returns {Promise<Object>} - Response data
     */
    async uploadFiles(endpoint, formData) {
        try {
            const response = await fetch(`${this.baseUrl}${endpoint}`, {
                method: 'POST',
                body: formData,
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('File upload failed:', error);
            throw error;
        }
    }

    /**
     * Delete a resource
     * @param {string} endpoint - API endpoint
     * @returns {Promise<Object>} - Response data
     */
    async delete(endpoint) {
        try {
            const response = await fetch(`${this.baseUrl}${endpoint}`, {
                method: 'DELETE',
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('DELETE request failed:', error);
            throw error;
        }
    }

    /**
     * Poll a task until it's completed or failed
     * @param {string} taskId - Task ID
     * @param {string} endpoint - API endpoint for checking task status
     * @param {number} interval - Polling interval in milliseconds
     * @param {number} timeout - Polling timeout in milliseconds
     * @returns {Promise<Object>} - Task result
     */
    async pollTask(taskId, endpoint, interval = 2000, timeout = 300000) {
        const startTime = Date.now();
        
        while (Date.now() - startTime < timeout) {
            const taskStatus = await this.get(`${endpoint}/${taskId}`);
            
            if (taskStatus.status === 'completed') {
                return taskStatus;
            } else if (taskStatus.status === 'failed') {
                throw new Error(`Task failed: ${taskStatus.message}`);
            }
            
            // Wait for the next poll
            await new Promise(resolve => setTimeout(resolve, interval));
        }
        
        throw new Error('Task polling timed out');
    }

    // API-specific methods

    /**
     * Check API health
     * @returns {Promise<Object>} - Health status
     */
    async checkHealth() {
        return this.get('/api/health');
    }

    /**
     * Get system information
     * @returns {Promise<Object>} - System information
     */
    async getSystemInfo() {
        return this.get('/api/utils/system');
    }

    /**
     * Get configuration information
     * @returns {Promise<Object>} - Configuration information
     */
    async getConfigInfo() {
        return this.get('/api/utils/config');
    }

    /**
     * Search for papers
     * @param {string} query - Search query
     * @param {Object} options - Search options
     * @returns {Promise<Object>} - Task information
     */
    async searchPapers(query, options = {}) {
        const data = {
            query,
            search_queries: options.searchQueries || 5,
            search_papers: options.searchPapers || 10,
            expand_papers: options.expandPapers || 10
        };
        
        return this.post('/api/search', data);
    }

    /**
     * Get paper information
     * @param {string} arxivId - arXiv ID
     * @returns {Promise<Object>} - Paper information
     */
    async getPaperInfo(arxivId) {
        return this.get(`/api/search/paper/${arxivId}`);
    }

    /**
     * Expand paper citations
     * @param {string} arxivId - arXiv ID
     * @param {number} depth - Expansion depth
     * @returns {Promise<Object>} - Task information
     */
    async expandCitations(arxivId, depth = 1) {
        return this.post('/api/search/expand', { arxiv_id: arxivId, depth });
    }

    /**
     * Generate review from arXiv IDs
     * @param {Array<string>} arxivIds - List of arXiv IDs
     * @param {Object} options - Review options
     * @returns {Promise<Object>} - Task information
     */
    async generateReviewFromArxiv(arxivIds, options = {}) {
        const data = {
            arxiv_ids: arxivIds,
            options: options
        };
        
        return this.post('/api/review/arxiv', data);
    }

    /**
     * Upload PDF files for review
     * @param {Array<File>} files - List of PDF files
     * @param {Object} options - Review options
     * @returns {Promise<Object>} - Task information
     */
    async uploadPdfsForReview(files, options = {}) {
        const formData = new FormData();
        
        files.forEach(file => {
            formData.append('files', file);
        });
        
        formData.append('options', JSON.stringify(options));
        
        return this.uploadFiles('/api/review/files', formData);
    }

    /**
     * Get task status
     * @param {string} taskId - Task ID
     * @param {string} type - Task type ('search' or 'review')
     * @returns {Promise<Object>} - Task status
     */
    async getTaskStatus(taskId, type = 'search') {
        const endpoint = type === 'review' ? '/api/review/task' : '/api/search/task';
        return this.get(`${endpoint}/${taskId}`);
    }

    /**
     * Wait for task completion
     * @param {string} taskId - Task ID
     * @param {string} type - Task type ('search' or 'review')
     * @returns {Promise<Object>} - Task result
     */
    async waitForTask(taskId, type = 'search') {
        const endpoint = type === 'review' ? '/api/review/task' : '/api/search/task';
        return this.pollTask(taskId, endpoint);
    }

    /**
     * Get all active tasks
     * @returns {Promise<Object>} - List of active tasks
     */
    async getTasks() {
        return this.get('/api/utils/tasks');
    }

    /**
     * Get all results
     * @returns {Promise<Object>} - List of results
     */
    async getResults() {
        return this.get('/api/utils/results');
    }

    /**
     * Delete a result file
     * @param {string} fileName - File name
     * @returns {Promise<Object>} - Deletion status
     */
    async deleteResult(fileName) {
        return this.delete(`/api/utils/results/${fileName}`);
    }

    /**
     * Clean temporary files
     * @returns {Promise<Object>} - Cleanup status
     */
    async cleanTemp() {
        return this.delete('/api/utils/temp');
    }
}

// Export the API client
window.ApiClient = ApiClient;
