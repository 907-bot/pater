// background.js - Service worker for Pater Extension

const API_BASE_URL = 'https://pater-api-xyz-asia-south1.run.app';

// Install event
chrome.runtime.onInstalled.addListener((details) => {
    if (details.reason === 'install') {
        // Open onboarding page
        chrome.tabs.create({ url: 'chrome-extension://' + chrome.runtime.id + '/onboarding.html' });
    }
});

// Message listener
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'getPrediction') {
        handlePrediction(request.data).then(sendResponse);
        return true; // Keep channel open for async
    } else if (request.action === 'syncWatchlist') {
        syncWatchlist(request.data).then(sendResponse);
        return true;
    } else if (request.action === 'getPriceHistory') {
        getPriceHistory(request.productId).then(sendResponse);
        return true;
    }
});

// Get prediction from API
async function handlePrediction(productData) {
    try {
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
            })
        });

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
            error: error.message
        };
    }
}

// Sync watchlist with backend
async function syncWatchlist(watchlist) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/watchlist/sync`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ products: watchlist })
        });

        return await response.json();
    } catch (error) {
        console.error('Sync error:', error);
        return { success: false };
    }
}

// Get price history
async function getPriceHistory(productId) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/prices/${productId}`);
        return await response.json();
    } catch (error) {
        console.error('Price history error:', error);
        return { success: false };
    }
}

// Periodic sync (every 6 hours)
chrome.alarms.create('syncWatchlist', { periodInMinutes: 360 });

chrome.alarms.onAlarm.addListener((alarm) => {
    if (alarm.name === 'syncWatchlist') {
        chrome.storage.sync.get('watchlist', (items) => {
            if (items.watchlist) {
                syncWatchlist(items.watchlist);
            }
        });
    }
});

// Context menu for quick add
chrome.contextMenus.create({
    id: 'addToWatchlist',
    title: 'Add to Pater Watchlist',
    contexts: ['link']
});

chrome.contextMenus.onClicked.addListener((info, tab) => {
    if (info.menuItemId === 'addToWatchlist') {
        // Extract product info from URL or page
        chrome.tabs.sendMessage(tab.id, {
            action: 'addCurrentToWatchlist'
        });
    }
});

// Badge update
function updateBadge() {
    chrome.storage.sync.get('watchlist', (items) => {
        const count = items.watchlist ? items.watchlist.length : 0;
        if (count > 0) {
            chrome.action.setBadgeText({ text: count.toString() });
            chrome.action.setBadgeBackgroundColor({ color: '#3b82f6' });
        }
    });
}

// Update badge on startup
updateBadge();

// Update badge when watchlist changes
chrome.storage.onChanged.addListener((changes, areaName) => {
    if (areaName === 'sync' && changes.watchlist) {
        updateBadge();
    }
});

// Log
console.log('🎯 Pater background service worker loaded');
