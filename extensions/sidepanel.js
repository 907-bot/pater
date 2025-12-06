// sidepanel.js - Detailed view logic

class PaterSidePanel {
    constructor() {
        this.currentProduct = null;
        this.watchlist = [];
        this.init();
    }

    async init() {
        this.setupTabNavigation();
        this.setupEventListeners();
        await this.loadData();
    }

    setupTabNavigation() {
        const tabBtns = document.querySelectorAll('.tab-btn');
        const tabPanes = document.querySelectorAll('.tab-pane');

        tabBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                // Remove active class from all
                tabBtns.forEach(b => b.classList.remove('active'));
                tabPanes.forEach(p => p.classList.remove('active'));

                // Add active to clicked
                btn.classList.add('active');
                const tabId = btn.getAttribute('data-tab');
                document.getElementById(tabId).classList.add('active');
            });
        });
    }

    setupEventListeners() {
        document.getElementById('close-btn').addEventListener('click', () => {
            window.close();
        });

        // Settings
        document.getElementById('notify-prices').addEventListener('change', (e) => {
            this.saveSetting('notifyPrices', e.target.checked);
        });
        document.getElementById('notify-sales').addEventListener('change', (e) => {
            this.saveSetting('notifySales', e.target.checked);
        });

        document.getElementById('export-btn').addEventListener('click', () => this.exportData());
        document.getElementById('clear-btn').addEventListener('click', () => this.clearData());

        document.getElementById('privacy-link').addEventListener('click', (e) => {
            e.preventDefault();
            chrome.tabs.create({ url: 'https://pater.example.com/privacy' });
        });

        document.getElementById('terms-link').addEventListener('click', (e) => {
            e.preventDefault();
            chrome.tabs.create({ url: 'https://pater.example.com/terms' });
        });

        // Watchlist search
        document.getElementById('watchlist-search').addEventListener('input', (e) => {
            this.filterWatchlist(e.target.value);
        });
    }

    async loadData() {
        // Get current product from message
        const message = await chrome.runtime.sendMessage({
            action: 'getCurrentProduct'
        });

        this.currentProduct = message?.product;
        this.watchlist = await Storage.get('watchlist') || [];

        if (this.currentProduct) {
            this.displayAnalysis();
            this.displayPriceHistory();
        }

        this.displayWatchlist();
        this.loadSettings();
    }

    displayAnalysis() {
        const current = 79999;
        const lowest = 59999;
        const avg = 69999;
        const savings = current - lowest;

        document.getElementById('detail-current-price').textContent = `₹ ${this.formatPrice(current)}`;
        document.getElementById('detail-lowest-price').textContent = `₹ ${this.formatPrice(lowest)}`;
        document.getElementById('detail-avg-price').textContent = `₹ ${this.formatPrice(avg)}`;
        document.getElementById('detail-savings').textContent = `₹ ${this.formatPrice(savings)}`;

        // Insights
        document.getElementById('market-trend').textContent = 'Price rising towards festival';
        document.getElementById('next-sale').textContent = 'Amazon Great Indian Festival (7 days)';
        document.getElementById('demand-level').textContent = 'Very High';
    }

    displayPriceHistory() {
        // Mock data
        const history = [
            { date: 'Today', price: 79999 },
            { date: 'Yesterday', price: 79999 },
            { date: '2 days ago', price: 75999 },
            { date: '3 days ago', price: 72999 },
            { date: '1 week ago', price: 69999 },
        ];

        const historyList = document.getElementById('history-list');
        historyList.innerHTML = history.map(h => `
            <div class="history-item">
                <span class="history-date">${h.date}</span>
                <span class="history-price">₹ ${this.formatPrice(h.price)}</span>
            </div>
        `).join('');
    }

    displayWatchlist() {
        const watchlistItems = document.getElementById('watchlist-items');

        if (this.watchlist.length === 0) {
            watchlistItems.innerHTML = '<p class="empty-message">Your watchlist is empty</p>';
            return;
        }

        watchlistItems.innerHTML = this.watchlist.map((item, index) => `
            <div class="watchlist-item">
                <div class="watchlist-item-info">
                    <div class="watchlist-item-name">${item.name}</div>
                    <div class="watchlist-item-price">₹ ${this.formatPrice(item.price)}</div>
                </div>
                <div class="watchlist-item-actions">
                    <button class="watchlist-item-btn" onclick="paterPanel.removeWatchlist(${index})">Remove</button>
                </div>
            </div>
        `).join('');
    }

    filterWatchlist(query) {
        const filtered = this.watchlist.filter(item =>
            item.name.toLowerCase().includes(query.toLowerCase())
        );

        const watchlistItems = document.getElementById('watchlist-items');
        if (filtered.length === 0) {
            watchlistItems.innerHTML = '<p class="empty-message">No products found</p>';
            return;
        }

        watchlistItems.innerHTML = filtered.map((item, index) => `
            <div class="watchlist-item">
                <div class="watchlist-item-info">
                    <div class="watchlist-item-name">${item.name}</div>
                    <div class="watchlist-item-price">₹ ${this.formatPrice(item.price)}</div>
                </div>
                <div class="watchlist-item-actions">
                    <button class="watchlist-item-btn">Remove</button>
                </div>
            </div>
        `).join('');
    }

    async removeWatchlist(index) {
        this.watchlist.splice(index, 1);
        await Storage.set('watchlist', this.watchlist);
        this.displayWatchlist();
    }

    formatPrice(price) {
        return new Intl.NumberFormat('en-IN').format(price);
    }

    async saveSetting(key, value) {
        const settings = await Storage.get('settings') || {};
        settings[key] = value;
        await Storage.set('settings', settings);
    }

    loadSettings() {
        Storage.get('settings').then(settings => {
            settings = settings || {};
            document.getElementById('notify-prices').checked = settings.notifyPrices !== false;
            document.getElementById('notify-sales').checked = settings.notifySales !== false;
            document.getElementById('price-drop-threshold').value = settings.priceDropThreshold || 10;
        });
    }

    exportData() {
        const data = {
            watchlist: this.watchlist,
            exportDate: new Date().toISOString()
        };

        const dataStr = JSON.stringify(data, null, 2);
        const blob = new Blob([dataStr], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `pater-watchlist-${Date.now()}.json`;
        a.click();
    }

    async clearData() {
        if (confirm('Are you sure you want to clear all data? This cannot be undone.')) {
            await Storage.set('watchlist', []);
            this.watchlist = [];
            this.displayWatchlist();
        }
    }
}

const paterPanel = new PaterSidePanel();
