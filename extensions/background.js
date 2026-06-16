// background.js - Service worker for Pater Extension

const DEFAULT_API_URL = 'https://pater-api-xyz-asia-south1.run.app';
let API_BASE_URL = DEFAULT_API_URL;

// Initialize on startup
chrome.runtime.onStartup.addListener(async () => {
    console.log('🎯 Pater extension starting up');
    await initializeExtension();
});

// Install event
chrome.runtime.onInstalled.addListener(async (details) => {
    console.log('🎯 Pater extension installed/updated');
    
    // Initialize storage with defaults
    await initializeExtension();
    
    if (details.reason === 'install') {
        // Open onboarding page on first install
        chrome.tabs.create({ url: chrome.runtime.getURL('onboarding.html') });
        
        // Set default settings
        await chrome.storage.sync.set({
            settings: {
                notifyPrices: true,
                notifySales: true,
                notifyRestocks: false,
                priceDropThreshold: 10,
                darkMode: false,
                compactMode: false
            },
            onboardingComplete: false
        });
    } else if (details.reason === 'update') {
        console.log('Pater updated to version:', chrome.runtime.getManifest().version);
    }
});

// Initialize extension
async function initializeExtension() {
    try {
        // Load API URL from storage or use default
        const storage = await chrome.storage.sync.get('apiUrl');
        API_BASE_URL = storage.apiUrl || DEFAULT_API_URL;
        
        // Update badge with watchlist count
        updateBadge();
        
        console.log('🎯 Pater background service worker loaded, API URL:', API_BASE_URL);
    } catch (error) {
        console.error('Failed to initialize extension:', error);
    }
}

// Message listener for communication with content scripts and popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    handleMessage(request, sender).then(sendResponse);
    return true; // Keep message channel open for async response
});

async function handleMessage(request, sender) {
    try {
        switch (request.action) {
            case 'getPrediction':
                return await handlePrediction(request.data);
            case 'syncWatchlist':
                return await syncWatchlist(request.data);
            case 'getPriceHistory':
                return await getPriceHistory(request.productId);
            case 'getAPIUrl':
                return { success: true, url: API_BASE_URL };
            case 'setAPIUrl':
                API_BASE_URL = request.url;
                await chrome.storage.sync.set({ apiUrl: request.url });
                return { success: true };
            case 'getCurrentProduct':
                return { product: null }; // Handled by content script
            case 'showNotification':
                return await showNotification(request.title, request.message);
            default:
                return { success: false, error: 'Unknown action' };
        }
    } catch (error) {
        console.error('Message handler error:', error);
        return { success: false, error: error.message };
    }
}

// Get prediction from API with timeout
async function handlePrediction(productData) {
    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 10000);

        const response = await fetch(`${API_BASE_URL}/api/predict`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                product_name: productData.name,
                current_price: productData.price,
                platform: productData.platform,
                category: productData.category
            }),
            signal: controller.signal
        });

        clearTimeout(timeoutId);

        if (!response.ok) {
            throw new Error(`API error: ${response.status}`);
        }

        const result = await response.json();
        return {
            success: true,
            data: result
        };
    } catch (error) {
        console.error('Prediction error:', error);
        return {
            success: false,
            error: error.message,
            offlinePrediction: getOfflinePrediction()
        };
    }
}

// Offline fallback prediction
function getOfflinePrediction() {
    return {
        festival_probability: Math.round(Math.random() * 30 + 10),
        expected_discount: Math.round(Math.random() * 25 + 5),
        recommendation: Math.random() > 0.5 ? 'buy' : 'wait',
        confidence: 0.65,
        isOffline: true
    };
}

// Sync watchlist with backend
async function syncWatchlist(watchlist) {
    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 10000);

        const response = await fetch(`${API_BASE_URL}/api/watchlist/sync`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ products: watchlist }),
            signal: controller.signal
        });

        clearTimeout(timeoutId);

        if (!response.ok) {
            throw new Error(`Sync error: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error('Sync error:', error);
        return { success: false, error: error.message };
    }
}

// Get price history
async function getPriceHistory(productId) {
    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 10000);

        const response = await fetch(`${API_BASE_URL}/api/prices/${productId}`, {
            signal: controller.signal
        });

        clearTimeout(timeoutId);

        if (!response.ok) {
            throw new Error(`Price history error: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error('Price history error:', error);
        return { success: false, error: error.message };
    }
}

// Show notification
async function showNotification(title, message) {
    try {
        // Check if notifications are enabled in settings
        const settings = await chrome.storage.sync.get('settings');
        const shouldNotify = settings.settings?.notifyPrices || 
                             settings.settings?.notifySales ||
                             settings.settings?.notifyRestocks;
        
        if (!shouldNotify) {
            return { success: false, reason: 'notifications disabled' };
        }

        await chrome.notifications.create({
            type: 'basic',
            iconUrl: 'icons/icon-48.png',
            title: title,
            message: message,
            priority: 2
        });

        return { success: true };
    } catch (error) {
        console.error('Notification error:', error);
        return { success: false, error: error.message };
    }
}

// Periodic sync (every 6 hours)
chrome.alarms.create('syncWatchlist', { periodInMinutes: 360 });

// Also check for price drops every hour
chrome.alarms.create('checkPriceDrops', { periodInMinutes: 60 });

chrome.alarms.onAlarm.addListener(async (alarm) => {
    if (alarm.name === 'syncWatchlist') {
        console.log('Running periodic watchlist sync');
        const items = await chrome.storage.sync.get('watchlist');
        if (items.watchlist && items.watchlist.length > 0) {
            await syncWatchlist(items.watchlist);
        }
    } else if (alarm.name === 'checkPriceDrops') {
        console.log('Checking for price drops');
        await checkPriceDrops();
    }
});

// Check for price drops in watchlist
async function checkPriceDrops() {
    try {
        const items = await chrome.storage.sync.get(['watchlist', 'settings']);
        const watchlist = items.watchlist || [];
        const settings = items.settings || {};
        
        if (!settings.notifyPrices || watchlist.length === 0) return;
        
        const threshold = settings.priceDropThreshold || 10;
        
        // This would normally fetch current prices from the API
        // For now, we'll just log that we're checking
        console.log(`Checking ${watchlist.length} items for price drops (threshold: ${threshold}%)`);
        
        // In production, you would:
        // 1. Fetch current prices for each item
        // 2. Compare with stored prices
        // 3. Send notification if price dropped below threshold
        
    } catch (error) {
        console.error('Price drop check error:', error);
    }
}

// Context menu for quick add
chrome.contextMenus.create({
    id: 'addToWatchlist',
    title: 'Add to Pater Watchlist',
    contexts: ['link', 'page']
});

chrome.contextMenus.onClicked.addListener((info, tab) => {
    if (info.menuItemId === 'addToWatchlist') {
        // Extract product info from URL or page
        chrome.tabs.sendMessage(tab.id, {
            action: 'addCurrentToWatchlist'
        }).catch(error => {
            console.error('Failed to send message to content script:', error);
        });
    }
});

// Badge update
async function updateBadge() {
    try {
        const items = await chrome.storage.sync.get('watchlist');
        const count = items.watchlist ? items.watchlist.length : 0;
        
        if (count > 0) {
            await chrome.action.setBadgeText({ text: count.toString() });
            await chrome.action.setBadgeBackgroundColor({ color: '#3b82f6' });
        } else {
            await chrome.action.setBadgeText({ text: '' });
        }
    } catch (error) {
        console.error('Badge update error:', error);
    }
}

// Update badge when watchlist changes
chrome.storage.onChanged.addListener((changes, areaName) => {
    if (areaName === 'sync' && changes.watchlist) {
        updateBadge();
    }
});

// Log startup
console.log('🎯 Pater background service worker initialized');
