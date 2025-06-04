/**
 * FIST Content Moderation JavaScript Client Library
 * 
 * A JavaScript/Node.js client library for easy integration with the FIST Content Moderation API.
 * Provides simple methods for content moderation, batch processing, and monitoring.
 * 
 * Usage:
 *   // Node.js
 *   const { FistClient } = require('./fist-client');
 *   
 *   // ES6 Modules / Browser
 *   import { FistClient } from './fist-client.js';
 *   
 *   const client = new FistClient({
 *     token: 'fist_your_token_here',
 *     baseUrl: 'https://your-fist-api.com'
 *   });
 *   
 *   // Single content moderation
 *   const result = await client.moderateContent('Some text to moderate');
 *   
 *   // Batch processing
 *   const results = await client.moderateBatch(['text1', 'text2', 'text3']);
 */

// Detect environment (Node.js vs Browser)
const isNode = typeof window === 'undefined' && typeof global !== 'undefined';
let fetch;

if (isNode) {
    // Node.js environment - try to import node-fetch
    try {
        fetch = require('node-fetch');
    } catch (e) {
        console.warn('node-fetch not found. Please install it: npm install node-fetch');
        throw new Error('node-fetch is required for Node.js environments');
    }
} else {
    // Browser environment - use native fetch
    fetch = window.fetch;
}

/**
 * Custom error classes for FIST client
 */
class FistClientError extends Error {
    constructor(message) {
        super(message);
        this.name = 'FistClientError';
    }
}

class AuthenticationError extends FistClientError {
    constructor(message = 'Authentication failed') {
        super(message);
        this.name = 'AuthenticationError';
    }
}

class APIError extends FistClientError {
    constructor(message, statusCode = null, responseData = null) {
        super(message);
        this.name = 'APIError';
        this.statusCode = statusCode;
        this.responseData = responseData;
    }
}

/**
 * Data classes for structured responses
 */
class ModerationResult {
    constructor(data) {
        this.moderationId = data.moderation_id;
        this.contentHash = data.content_hash;
        this.inappropriateProbability = data.ai_result.inappropriate_probability;
        this.aiReason = data.ai_result.reason;
        this.finalDecision = data.final_decision;
        this.reason = data.reason;
        this.wordCount = data.word_count;
        this.percentageUsed = data.percentage_used;
        this.createdAt = data.created_at;
        this.fromCache = data.from_cache || false;
    }
}

class BatchJob {
    constructor(data) {
        this.jobId = data.job_id;
        this.status = data.status;
        this.totalItems = data.total_items;
        this.processedItems = data.processed_items;
        this.progressPercent = data.progress_percent;
        this.createdAt = data.created_at;
        this.startedAt = data.started_at || null;
        this.completedAt = data.completed_at || null;
        this.backgroundTaskId = data.background_task_id || null;
    }
}

/**
 * Main FIST Client class
 */
class FistClient {
    /**
     * Initialize FIST client
     * 
     * @param {Object} options - Configuration options
     * @param {string} options.token - API token (should start with 'fist_')
     * @param {string} [options.baseUrl='http://localhost:8000'] - Base URL of the FIST API
     * @param {number} [options.timeout=30000] - Request timeout in milliseconds
     * @param {number} [options.maxRetries=3] - Maximum number of retries for failed requests
     * @param {number} [options.retryDelay=1000] - Delay between retries in milliseconds
     */
    constructor(options = {}) {
        const {
            token,
            baseUrl = 'http://localhost:8000',
            timeout = 30000,
            maxRetries = 3,
            retryDelay = 1000
        } = options;

        if (!token) {
            throw new Error('Token is required');
        }

        if (!token.startsWith('fist_')) {
            throw new Error('Token must start with "fist_"');
        }

        this.token = token;
        this.baseUrl = baseUrl.replace(/\/$/, ''); // Remove trailing slash
        this.timeout = timeout;
        this.maxRetries = maxRetries;
        this.retryDelay = retryDelay;

        this.defaultHeaders = {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
            'User-Agent': 'FIST-JavaScript-Client/1.0.0'
        };
    }

    /**
     * Make HTTP request with retry logic
     * 
     * @private
     * @param {string} method - HTTP method
     * @param {string} endpoint - API endpoint
     * @param {Object} [data] - Request body data
     * @param {Object} [params] - URL parameters
     * @returns {Promise<Object>} Response data
     */
    async _makeRequest(method, endpoint, data = null, params = null) {
        const url = new URL(endpoint, this.baseUrl);
        
        if (params) {
            Object.keys(params).forEach(key => {
                url.searchParams.append(key, params[key]);
            });
        }

        const requestOptions = {
            method: method.toUpperCase(),
            headers: { ...this.defaultHeaders },
            timeout: this.timeout
        };

        if (data && ['POST', 'PUT', 'PATCH'].includes(method.toUpperCase())) {
            requestOptions.body = JSON.stringify(data);
        }

        for (let attempt = 0; attempt <= this.maxRetries; attempt++) {
            try {
                const response = await fetch(url.toString(), requestOptions);

                // Handle authentication errors
                if (response.status === 401) {
                    throw new AuthenticationError('Invalid or expired token');
                }

                // Handle other client/server errors
                if (response.status >= 400) {
                    let errorMessage;
                    let errorData = null;

                    try {
                        errorData = await response.json();
                        errorMessage = errorData.detail || `HTTP ${response.status}`;
                    } catch {
                        errorMessage = `HTTP ${response.status}: ${response.statusText}`;
                    }

                    throw new APIError(errorMessage, response.status, errorData);
                }

                return await response.json();

            } catch (error) {
                if (attempt === this.maxRetries) {
                    throw error;
                }

                // Don't retry client errors (4xx)
                if (error instanceof APIError && error.statusCode < 500) {
                    throw error;
                }

                // Exponential backoff
                await this._sleep(this.retryDelay * Math.pow(2, attempt));
            }
        }

        throw new APIError('Max retries exceeded');
    }

    /**
     * Sleep utility function
     * 
     * @private
     * @param {number} ms - Milliseconds to sleep
     * @returns {Promise<void>}
     */
    _sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    /**
     * Moderate a single piece of content
     * 
     * @param {string} content - Text content to moderate
     * @param {Object} [options] - Moderation options
     * @param {number[]} [options.percentages] - Custom percentages for content piercing
     * @param {number[]} [options.thresholds] - Custom word count thresholds
     * @param {Object} [options.probabilityThresholds] - Custom probability thresholds
     * @returns {Promise<ModerationResult>} Moderation result
     */
    async moderateContent(content, options = {}) {
        if (!content || !content.trim()) {
            throw new Error('Content cannot be empty');
        }

        const data = { content };
        
        if (options.percentages) data.percentages = options.percentages;
        if (options.thresholds) data.thresholds = options.thresholds;
        if (options.probabilityThresholds) data.probability_thresholds = options.probabilityThresholds;

        const response = await this._makeRequest('POST', '/api/moderate', data);
        return new ModerationResult(response.result);
    }

    /**
     * Moderate multiple pieces of content in batch
     * 
     * @param {string[]} contents - Array of text content to moderate
     * @param {Object} [options] - Batch processing options
     * @param {number[]} [options.percentages] - Custom percentages for content piercing
     * @param {number[]} [options.thresholds] - Custom word count thresholds
     * @param {Object} [options.probabilityThresholds] - Custom probability thresholds
     * @param {boolean} [options.background=false] - Process in background
     * @param {number} [options.pollInterval=2000] - Polling interval for background jobs (ms)
     * @param {number} [options.maxWaitTime=300000] - Maximum time to wait for background jobs (ms)
     * @returns {Promise<ModerationResult[]|BatchJob>} Array of results or BatchJob object
     */
    async moderateBatch(contents, options = {}) {
        if (!contents || contents.length === 0) {
            throw new Error('Contents array cannot be empty');
        }

        if (contents.length > 100) {
            throw new Error('Batch size cannot exceed 100 items');
        }

        const {
            percentages,
            thresholds,
            probabilityThresholds,
            background = false,
            pollInterval = 2000,
            maxWaitTime = 300000
        } = options;

        const data = {
            contents,
            background
        };

        if (percentages) data.percentages = percentages;
        if (thresholds) data.thresholds = thresholds;
        if (probabilityThresholds) data.probability_thresholds = probabilityThresholds;

        const response = await this._makeRequest('POST', '/api/moderate/batch', data);

        if (background) {
            const batchJob = new BatchJob(response);
            
            // Wait for completion if requested
            if (maxWaitTime > 0) {
                return await this._waitForBatchCompletion(batchJob.jobId, pollInterval, maxWaitTime);
            }
            
            return batchJob;
        } else {
            // Return results directly
            return (response.results || []).map(result => new ModerationResult(result));
        }
    }

    /**
     * Get status of a batch processing job
     * 
     * @param {string} jobId - Batch job ID
     * @returns {Promise<BatchJob>} Batch job status
     */
    async getBatchStatus(jobId) {
        const response = await this._makeRequest('GET', `/api/moderate/batch/${jobId}/status`);
        return new BatchJob(response);
    }

    /**
     * Get results of a completed batch job
     * 
     * @param {string} jobId - Batch job ID
     * @returns {Promise<ModerationResult[]>} Array of moderation results
     */
    async getBatchResults(jobId) {
        const response = await this._makeRequest('GET', `/api/moderate/batch/${jobId}/results`);
        return (response.results || []).map(result => new ModerationResult(result));
    }

    /**
     * Wait for batch job completion and return results
     * 
     * @private
     * @param {string} jobId - Batch job ID
     * @param {number} pollInterval - Polling interval in milliseconds
     * @param {number} maxWaitTime - Maximum wait time in milliseconds
     * @returns {Promise<ModerationResult[]>} Array of moderation results
     */
    async _waitForBatchCompletion(jobId, pollInterval, maxWaitTime) {
        const startTime = Date.now();

        while (Date.now() - startTime < maxWaitTime) {
            const status = await this.getBatchStatus(jobId);

            if (status.status === 'completed') {
                return await this.getBatchResults(jobId);
            } else if (status.status === 'failed') {
                throw new APIError(`Batch job ${jobId} failed`);
            }

            await this._sleep(pollInterval);
        }

        throw new APIError(`Batch job ${jobId} did not complete within ${maxWaitTime}ms`);
    }

    /**
     * Get system health status
     * 
     * @returns {Promise<Object>} Health check results
     */
    async getHealth() {
        return await this._makeRequest('GET', '/api/health');
    }

    /**
     * Get system performance metrics
     * 
     * @returns {Promise<Object>} Performance metrics
     */
    async getMetrics() {
        return await this._makeRequest('GET', '/api/metrics');
    }

    /**
     * Get cache performance statistics
     * 
     * @returns {Promise<Object>} Cache statistics
     */
    async getCacheStats() {
        return await this._makeRequest('GET', '/api/cache/stats');
    }

    /**
     * Clear the system cache
     * 
     * @returns {Promise<Object>} Clear operation results
     */
    async clearCache() {
        return await this._makeRequest('DELETE', '/api/cache/clear');
    }

    /**
     * Test connection to the FIST API
     * 
     * @returns {Promise<boolean>} True if connection is successful
     */
    async testConnection() {
        try {
            const health = await this.getHealth();
            return ['healthy', 'warning'].includes(health.status);
        } catch {
            return false;
        }
    }
}

/**
 * Convenience functions for quick usage
 */

/**
 * Quick function to moderate a single piece of content
 * 
 * @param {string} content - Text content to moderate
 * @param {string} token - API token
 * @param {string} [baseUrl='http://localhost:8000'] - Base URL of the FIST API
 * @param {Object} [options] - Additional moderation options
 * @returns {Promise<ModerationResult>} Moderation result
 */
async function moderateContent(content, token, baseUrl = 'http://localhost:8000', options = {}) {
    const client = new FistClient({ token, baseUrl });
    return await client.moderateContent(content, options);
}

/**
 * Quick function to moderate multiple pieces of content
 * 
 * @param {string[]} contents - Array of text content to moderate
 * @param {string} token - API token
 * @param {string} [baseUrl='http://localhost:8000'] - Base URL of the FIST API
 * @param {Object} [options] - Additional moderation options
 * @returns {Promise<ModerationResult[]>} Array of moderation results
 */
async function moderateBatch(contents, token, baseUrl = 'http://localhost:8000', options = {}) {
    const client = new FistClient({ token, baseUrl });
    return await client.moderateBatch(contents, options);
}

// Export for different module systems
if (isNode) {
    // Node.js CommonJS
    module.exports = {
        FistClient,
        ModerationResult,
        BatchJob,
        FistClientError,
        AuthenticationError,
        APIError,
        moderateContent,
        moderateBatch
    };
} else {
    // Browser ES6 modules or global
    if (typeof window !== 'undefined') {
        window.FistClient = FistClient;
        window.moderateContent = moderateContent;
        window.moderateBatch = moderateBatch;
    }
}

// ES6 module export (for modern environments)
export {
    FistClient,
    ModerationResult,
    BatchJob,
    FistClientError,
    AuthenticationError,
    APIError,
    moderateContent,
    moderateBatch
};

// Example usage
if (isNode && require.main === module) {
    // Example usage when run directly in Node.js
    (async () => {
        const client = new FistClient({
            token: 'fist_your_token_here',
            baseUrl: 'http://localhost:8000'
        });

        try {
            // Test connection
            if (await client.testConnection()) {
                console.log('✅ Connected to FIST API successfully');

                // Single content moderation
                const result = await client.moderateContent('This is a test message');
                console.log(`Moderation result: ${result.finalDecision} (${result.inappropriateProbability}%)`);

                // Batch processing
                const contents = ['Message 1', 'Message 2', 'Message 3'];
                const results = await client.moderateBatch(contents);
                console.log(`Batch processed ${results.length} items`);

                // System health
                const health = await client.getHealth();
                console.log(`System health: ${health.status}`);

            } else {
                console.log('❌ Failed to connect to FIST API');
            }
        } catch (error) {
            console.error('Error:', error.message);
        }
    })();
}
