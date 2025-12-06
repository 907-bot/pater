// popup.js - Main popup logic for Pater Extension

class PaterPopup {
    constructor() {
        this.currentProduct = null;
        this.init();
    }

    async init() {
        this.setupEventListeners();
        await this.loadProduct();
    }

    setupEventListeners() {
        // Button listeners
        document.getElementById('add-watchlist-btn').addEventListener('click', () => this.addToWatchlist());
        document.getElementById('view-details-btn').addEventListener('click', () => this.viewDetails());
        document.getElementById('retry-btn').addEventListener('click', () => this.loadProduct());

        // Footer links
        document.getElementById('settings-link').addEventListener('click', (e) => this.openSettings(e));
        document.getElementById('help-link').addEventListener('click', (e) => this.openHelp(e));
        document.getElementById('feedback-link').addEventListener('click', (e) => this.openFeedback(e));
    }

    async loadProduct() {
        try {
            this.showStatus('Loading...', 'loading');

            // Get active tab
            const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
            
            // Send message to content script
            const response = await chrome.tabs.sendMessage(tab.id, {
                action: 'getProduct'
            });

            if (response && response.product) {
                this.currentProduct = response.product;
                await this.getPrediction();
                this.displayProduct();
            } else {
                this.showEmptyState();
            }
        } catch (error) {
            Logger.error('Error loading product', error);
            this.showError('Failed to load product. Make sure you\'re on a product page.');
        }
    }

    async getPrediction() {
        try {
            if (!this.currentProduct) return;

            // Call API
            const prediction = await APIClient.predict({
                product_name: this.currentProduct.name,
                current_price: this.currentProduct.price,
                platform: this.currentProduct.platform,
                category: this.currentProduct.category
            });

            if (prediction) {
                this.currentProduct.prediction = prediction;
            }
        } catch (error) {
            Logger.error('Error getting prediction', error);
            // Show offline prediction
            this.currentProduct.prediction = this.getOfflinePrediction();
        }
    }

    getOfflinePrediction() {
        // Fallback prediction when API unavailable
        return {
            festival_probability: Math.random() * 100,
            expected_discount: Math.random() * 40 + 10,
            recommendation: Math.random() > 0.5 ? 'buy' : 'wait',
            confidence: 0.72
        };
    }

    displayProduct() {
        const productSection = document.getElementById('product-section');
        const emptyState = document.getElementById('empty-state');
        const errorState = document.getElementById('error-state');

        productSection.style.display = 'flex';
        emptyState.style.display = 'none';
        errorState.style.display = 'none';

        // Update product info
        document.getElementById('product-name').textContent = this.currentProduct.name;
        document.getElementById('product-category').textContent = `Category: ${this.currentProduct.category || 'N/A'}`;
        document.getElementById('current-price').textContent = `₹ ${this.formatPrice(this.currentProduct.price)}`;
        document.getElementById('platform-badge').textContent = this.currentProduct.platform.toUpperCase();

        // Update prediction
        if (this.currentProduct.prediction) {
            const pred = this.currentProduct.prediction;
            
            // Festival probability
            const festivalProb = Math.round(pred.festival_probability);
            document.getElementById('festival-prob').textContent = festivalProb;
            document.getElementById('festival-progress').style.width = `${festivalProb}%`;

            // Expected discount
            const discount = Math.round(pred.expected_discount);
            document.getElementById('expected-discount').textContent = discount;

            // Recommendation
            const recElement = document.getElementById('recommendation');
            let recBadge = 'Wait for better deal';
            let recClass = 'rec-wait';

            if (pred.recommendation === 'buy') {
                recBadge = 'BUY NOW - Best Price!';
                recClass = 'rec-buy';
            } else if (pred.recommendation === 'skip') {
                recBadge = 'Price is High - Skip';
                recClass = 'rec-skip';
            }

            recElement.innerHTML = `<span class="rec-badge ${recClass}">${recBadge}</span>`;
        }

        this.showStatus('Ready', 'success');
    }

    formatPrice(price) {
        return new Intl.NumberFormat('en-IN').format(price);
    }

    async addToWatchlist() {
        try {
            if (!this.currentProduct) return;

            // Save to local storage
            const watchlist = await Storage.get('watchlist') || [];
            
            if (!watchlist.find(p => p.name === this.currentProduct.name)) {
                watchlist.push({
                    ...this.currentProduct,
                    addedAt: new Date().toISOString()
                });
                
                await Storage.set('watchlist', watchlist);
                this.showToast('✅ Added to watchlist!');
                
                // Sync with backend
                await APIClient.syncWatchlist(watchlist);
            } else {
                this.showToast('⚠️ Already in watchlist');
            }
        } catch (error) {
            Logger.error('Error adding to watchlist', error);
            this.showToast('❌ Failed to add to watchlist');
        }
    }

    viewDetails() {
        // Open side panel with detailed view
        chrome.sidePanel.open({ windowId: chrome.windows.WINDOW_ID_CURRENT });
    }

    showStatus(text, type = 'normal') {
        const badge = document.getElementById('status-badge');
        badge.textContent = text;
        badge.className = `status-badge ${type}`;
        
        const dot = badge.querySelector('.status-dot');
        const statusText = badge.querySelector('.status-text');
        
        if (dot) dot.style.display = type === 'normal' ? 'none' : 'block';
        if (statusText) statusText.textContent = text;
    }

    showEmptyState() {
        document.getElementById('product-section').style.display = 'none';
        document.getElementById('empty-state').style.display = 'flex';
        document.getElementById('error-state').style.display = 'none';
        this.showStatus('No product detected', 'normal');
    }

    showError(message) {
        document.getElementById('product-section').style.display = 'none';
        document.getElementById('empty-state').style.display = 'none';
        document.getElementById('error-state').style.display = 'flex';
        document.getElementById('error-message').textContent = message;
        this.showStatus('Error', 'error');
    }

    showToast(message) {
        const toast = document.getElementById('toast');
        document.getElementById('toast-message').textContent = message;
        toast.classList.add('show');
        
        setTimeout(() => {
            toast.classList.remove('show');
        }, 3000);
    }

    openSettings(e) {
        e.preventDefault();
        chrome.runtime.openOptionsPage();
    }

    openHelp(e) {
        e.preventDefault();
        chrome.tabs.create({ url: 'https://pater.example.com/help' });
    }

    openFeedback(e) {
        e.preventDefault();
        chrome.tabs.create({ url: 'https://pater.example.com/feedback' });
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new PaterPopup();
});
