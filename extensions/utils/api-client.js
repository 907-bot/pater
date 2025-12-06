// api-client.js - API communication utilities

class APIClient {
    static API_BASE_URL = 'https://pater-api-xyz-asia-south1.run.app';
    static API_KEY = null;

    static async init() {
        // Load API key from storage
        const storage = await chrome.storage.sync.get('apiKey');
        this.API_KEY = storage.apiKey || null;
    }

    static async request(endpoint, options = {}) {
        try {
            const url = `${this.API_BASE_URL}${endpoint}`;
            const headers = {
                'Content-Type': 'application/json',
                ...(this.API_KEY && { 'X-API-Key': this.API_KEY })
            };

            const response = await fetch(url, {
                ...options,
                headers: { ...headers, ...options.headers }
            });

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
            return await this.request('/health', { method: 'GET' });
        } catch {
            return { status: 'error' };
        }
    }
}

// Initialize on load
if (typeof window !== 'undefined') {
    APIClient.init();
}
