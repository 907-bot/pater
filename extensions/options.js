// options.js - Settings page logic for Pater Extension

class PaterOptions {
    constructor() {
        this.apiUrl = '';
        this.init();
    }

    async init() {
        Logger.info('Initializing options page');
        await this.loadSettings();
        this.setupEventListeners();
        this.updateWatchlistCount();
        this.checkAPIStatus();
    }

    setupEventListeners() {
        // Link handlers
        document.getElementById('privacy-link').addEventListener('click', (e) => {
            e.preventDefault();
            chrome.tabs.create({ url: 'https://pater.example.com/privacy' });
        });

        document.getElementById('terms-link').addEventListener('click', (e) => {
            e.preventDefault();
            chrome.tabs.create({ url: 'https://pater.example.com/terms' });
        });

        document.getElementById('help-link').addEventListener('click', (e) => {
            e.preventDefault();
            chrome.tabs.create({ url: 'https://pater.example.com/help' });
        });

        // API URL input - update status on change
        document.getElementById('api-url').addEventListener('input', () => {
            this.updateAPIStatusIndicator('checking');
        });
    }

    async loadSettings() {
        try {
            // Load API URL
            const apiUrl = await Storage.get('apiUrl');
            if (apiUrl) {
                this.apiUrl = apiUrl;
                document.getElementById('api-url').value = apiUrl;
                // Update APIClient
                APIClient.API_BASE_URL = apiUrl;
            }

            // Load notification settings
            const settings = await Storage.get('settings') || {};
            
            document.getElementById('notify-prices').checked = settings.notifyPrices !== false;
            document.getElementById('notify-sales').checked = settings.notifySales !== false;
            document.getElementById('notify-restocks').checked = settings.notifyRestocks === true;
            document.getElementById('price-threshold').value = settings.priceDropThreshold || 10;

            // Load appearance settings
            document.getElementById('dark-mode').checked = settings.darkMode === true;
            document.getElementById('compact-mode').checked = settings.compactMode === true;

            Logger.info('Settings loaded successfully');
        } catch (error) {
            Logger.error('Error loading settings', error);
            this.showToast('Failed to load settings', 'error');
        }
    }

    async saveSettings(key, value) {
        const settings = await Storage.get('settings') || {};
        settings[key] = value;
        await Storage.set('settings', settings);
    }

    // API Configuration
    async testAPI() {
        const apiUrl = document.getElementById('api-url').value.trim();
        
        if (!apiUrl) {
            this.showToast('Please enter an API URL', 'error');
            return;
        }

        this.updateAPIStatusIndicator('checking');

        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 5000);

            const response = await fetch(`${apiUrl}/health`, {
                method: 'GET',
                signal: controller.signal
            });

            clearTimeout(timeoutId);

            if (response.ok) {
                this.updateAPIStatusIndicator('connected');
                this.showToast('✅ API connection successful!', 'success');
            } else {
                this.updateAPIStatusIndicator('disconnected');
                this.showToast('API returned error: ' + response.status, 'error');
            }
        } catch (error) {
            this.updateAPIStatusIndicator('disconnected');
            Logger.error('API test failed', error);
            
            if (error.name === 'AbortError') {
                this.showToast('Connection timeout - please check the URL', 'error');
            } else {
                this.showToast('Failed to connect to API', 'error');
            }
        }
    }

    async saveAPI() {
        const apiUrl = document.getElementById('api-url').value.trim();
        
        if (!apiUrl) {
            this.showToast('Please enter an API URL', 'error');
            return;
        }

        // Validate URL format
        try {
            new URL(apiUrl);
        } catch {
            this.showToast('Invalid URL format', 'error');
            return;
        }

        this.apiUrl = apiUrl;
        await Storage.set('apiUrl', apiUrl);
        
        // Update APIClient
        APIClient.API_BASE_URL = apiUrl;

        this.showToast('API settings saved!', 'success');
        this.checkAPIStatus();
    }

    checkAPIStatus() {
        this.testAPI();
    }

    updateAPIStatusIndicator(status) {
        const badge = document.getElementById('api-status');
        const text = document.getElementById('status-text');
        
        badge.className = 'status-badge';
        
        switch (status) {
            case 'connected':
                badge.classList.add('connected');
                text.textContent = 'Connected';
                break;
            case 'disconnected':
                badge.classList.add('disconnected');
                text.textContent = 'Disconnected';
                break;
            case 'checking':
            default:
                badge.classList.add('disconnected');
                text.textContent = 'Checking...';
                break;
        }
    }

    // Notifications
    async saveNotifications() {
        const settings = {
            notifyPrices: document.getElementById('notify-prices').checked,
            notifySales: document.getElementById('notify-sales').checked,
            notifyRestocks: document.getElementById('notify-restocks').checked,
            priceDropThreshold: parseInt(document.getElementById('price-threshold').value) || 10
        };

        await Storage.set('settings', settings);
        
        // Update Chrome notification permissions based on settings
        if (settings.notifyPrices || settings.notifySales || settings.notifyRestocks) {
            // Notifications are enabled - good to go
            Logger.info('Notifications enabled');
        }

        this.showToast('Notification settings saved!', 'success');
    }

    // Appearance
    async saveAppearance() {
        const darkMode = document.getElementById('dark-mode').checked;
        const compactMode = document.getElementById('compact-mode').checked;

        const settings = await Storage.get('settings') || {};
        settings.darkMode = darkMode;
        settings.compactMode = compactMode;
        await Storage.set('settings', settings);

        // Apply theme immediately
        this.applyTheme(darkMode);

        this.showToast('Appearance settings saved!', 'success');
    }

    applyTheme(darkMode) {
        if (darkMode) {
            document.documentElement.setAttribute('data-color-scheme', 'dark');
        } else {
            document.documentElement.removeAttribute('data-color-scheme');
        }
    }

    // Data Management
    async updateWatchlistCount() {
        try {
            const watchlist = await Storage.get('watchlist') || [];
            document.getElementById('watchlist-count').textContent = 
                `${watchlist.length} product${watchlist.length !== 1 ? 's' : ''} in your watchlist`;
        } catch (error) {
            document.getElementById('watchlist-count').textContent = 'Unable to load count';
        }
    }

    async exportData() {
        try {
            const data = {
                watchlist: await Storage.get('watchlist') || [],
                settings: await Storage.get('settings') || {},
                apiUrl: await Storage.get('apiUrl') || '',
                exportDate: new Date().toISOString(),
                version: '0.1.0'
            };

            const dataStr = JSON.stringify(data, null, 2);
            const blob = new Blob([dataStr], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            
            const a = document.createElement('a');
            a.href = url;
            a.download = `pater-backup-${Date.now()}.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);

            this.showToast('Data exported successfully!', 'success');
        } catch (error) {
            Logger.error('Export failed', error);
            this.showToast('Failed to export data', 'error');
        }
    }

    async clearData() {
        const confirmed = confirm(
            'Are you sure you want to clear all data?\n\n' +
            'This will delete:\n' +
            '• Your entire watchlist\n' +
            '• All saved settings\n' +
            '• Price history\n\n' +
            'This action cannot be undone.'
        );

        if (!confirmed) return;

        try {
            await Storage.clear();
            await this.loadSettings();
            this.updateWatchlistCount();
            this.showToast('All data cleared!', 'success');
            
            Logger.info('All extension data cleared');
        } catch (error) {
            Logger.error('Clear data failed', error);
            this.showToast('Failed to clear data', 'error');
        }
    }

    // Toast notification
    showToast(message, type = 'normal') {
        const toast = document.getElementById('toast');
        const toastMessage = document.getElementById('toast-message');
        
        toastMessage.textContent = message;
        toast.className = 'toast';
        
        if (type === 'success') {
            toast.classList.add('success');
        } else if (type === 'error') {
            toast.classList.add('error');
        }

        toast.classList.add('show');

        setTimeout(() => {
            toast.classList.remove('show');
        }, 3000);
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new PaterOptions();
});

// Apply initial theme
const settingsStored = Storage.get('settings').then(settings => {
    if (settings && settings.darkMode) {
        document.documentElement.setAttribute('data-color-scheme', 'dark');
    }
});