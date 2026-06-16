// api-client.js - API communication utilities

class APIClient {
    static API_BASE_URL = 'https://pater-api-xyz-asia-south1.run.app';
    static API_KEY = null;
    static DEFAULT_API_URL = 'https://pater-api-xyz-asia-south1.run.app';
    static initialized = false;

    static async init() {
        if (this.initialized) return;
        
        try {
            // Load API URL from storage
            const storage = await chrome.storage.sync.get('apiUrl');
            if (storage.apiUrl) {
                this.API_BASE_URL = storage.apiUrl;
            }
            
            // Load API key from storage
            const keyStorage = await chrome.storage.sync.get('apiKey');
            this.API_KEY = keyStorage.apiKey || null;
            
            this.initialized = true;
            Logger.info('APIClient initialized with URL:', this.API_BASE_URL);
        } catch (error) {
            Logger.error('Failed to initialize APIClient', error);
        }
    }

    static async request(endpoint, options = {}) {
        try {
            // Ensure URL is loaded from storage
            if (!this.initialized) {
                await this.init();
            }

            const url = `${this.API_BASE_URL}${endpoint}`;
            const headers = {
                'Content-Type': 'application/json',
                ...(this.API_KEY && { 'X-API-Key': this.API_KEY })
            };

            // Add timeout handling
            const controller = new AbortController();
            const timeout = options.timeout || 10000;
            const timeoutId = setTimeout(() => controller.abort(), timeout);

            const response = await fetch(url, {
                ...options,
                headers: { ...headers, ...options.headers },
                signal: controller.signal
            });

            clearTimeout(timeoutId);

            if (!response.ok) {
                throw new Error(`API Error: ${response.status} ${response.statusText}`);
            }

            return await response.json();
        } catch (error) {
            Logger.error(`API request failed: ${endpoint}`, error);
            throw error;
        }
    }

    static async predict(productData) {
        return this.request('/api/predict', {
            method: 'POST',
            body: JSON.stringify(productData)
        });
    }

    static async getPriceHistory(productId) {
        return this.request(`/api/prices/${productId}`, {
            method: 'GET'
        });
    }

    static async addToWatchlist(product) {
        return this.request('/api/watchlist/add', {
            method: 'POST',
            body: JSON.stringify(product)
        });
    }

    static async syncWatchlist(watchlist) {
        return this.request('/api/watchlist/sync', {
            method: 'POST',
            body: JSON.stringify({ products: watchlist })
        });
    }

    static async getWatchlist() {
        return this.request('/api/watchlist', {
            method: 'GET'
        });
    }

    static async createPriceAlert(productId, threshold) {
        return this.request('/api/prices/alert', {
            method: 'POST',
            body: JSON.stringify({
                product_id: productId,
                threshold: threshold
            })
        });
    }

    static async getAnalytics() {
        return this.request('/api/analytics/savings', {
            method: 'GET'
        });
    }

    static async getFestivals() {
        return this.request('/api/festivals', {
            method: 'GET'
        });
    }

    static async health() {
        try {
            return await this.request('/health', { method: 'GET', timeout: 5000 });
        } catch {
            return { status: 'error' };
        }
    }

    static async updateBaseUrl(newUrl) {
        this.API_BASE_URL = newUrl;
        await chrome.storage.sync.set({ apiUrl: newUrl });
        Logger.info('API Base URL updated to:', newUrl);
    }

    static getBaseUrl() {
        return this.API_BASE_URL;
    }
}

// Initialize on load for background script context
if (typeof chrome !== 'undefined' && chrome.runtime && chrome.runtime.id) {
    APIClient.init();
}
