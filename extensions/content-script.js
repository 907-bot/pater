// content-script.js - Runs on e-commerce websites

class ProductDetector {
    constructor() {
        this.platform = this.detectPlatform();
        this.product = null;
        this.init();
    }

    init() {
        this.extractProduct();
        this.setupListeners();
    }

    detectPlatform() {
        const hostname = window.location.hostname;
        if (hostname.includes('amazon.in')) return 'amazon';
        if (hostname.includes('flipkart.com')) return 'flipkart';
        if (hostname.includes('myntra.com')) return 'myntra';
        return null;
    }

    extractProduct() {
        if (this.platform === 'amazon') {
            this.extractAmazonProduct();
        } else if (this.platform === 'flipkart') {
            this.extractFlipkartProduct();
        } else if (this.platform === 'myntra') {
            this.extractMyntraProduct();
        }
    }

    extractAmazonProduct() {
        try {
            const title = document.querySelector('#productTitle')?.textContent?.trim();
            const priceText = document.querySelector('.a-price-whole')?.textContent;
            const price = parseInt(priceText?.replace(/[^0-9]/g, '')) || 0;
            
            // Category from breadcrumb
            const category = document.querySelector('.a-breadcrumb span')?.textContent?.trim() || 'Electronics';

            if (title && price > 0) {
                this.product = {
                    name: title,
                    price: price,
                    category: category,
                    platform: 'amazon',
                    url: window.location.href,
                    productId: this.extractAmazonProductId()
                };
            }
        } catch (error) {
            console.error('Error extracting Amazon product:', error);
        }
    }

    extractFlipkartProduct() {
        try {
            const title = document.querySelector('[data-qa="title"]')?.textContent?.trim() ||
                         document.querySelector('span.B_NuCI')?.textContent?.trim();
            
            const priceText = document.querySelector('[data-qa="price"]')?.textContent ||
                            document.querySelector('._30jeq3._16Jk6d')?.textContent;
            const price = parseInt(priceText?.replace(/[^0-9]/g, '')) || 0;

            const category = 'Electronics'; // Flipkart breadcrumb extraction

            if (title && price > 0) {
                this.product = {
                    name: title,
                    price: price,
                    category: category,
                    platform: 'flipkart',
                    url: window.location.href,
                    productId: this.extractFlipkartProductId()
                };
            }
        } catch (error) {
            console.error('Error extracting Flipkart product:', error);
        }
    }

    extractMyntraProduct() {
        try {
            const title = document.querySelector('.productTitle')?.textContent?.trim();
            const priceText = document.querySelector('.productDiscountedPriceText')?.textContent;
            const price = parseInt(priceText?.replace(/[^0-9]/g, '')) || 0;

            const category = document.querySelector('.breadcrumbs')?.textContent?.trim() || 'Fashion';

            if (title && price > 0) {
                this.product = {
                    name: title,
                    price: price,
                    category: category,
                    platform: 'myntra',
                    url: window.location.href,
                    productId: this.extractMyntraProductId()
                };
            }
        } catch (error) {
            console.error('Error extracting Myntra product:', error);
        }
    }

    extractAmazonProductId() {
        const match = window.location.href.match(/\/dp\/([A-Z0-9]+)/);
        return match ? match[1] : null;
    }

    extractFlipkartProductId() {
        const match = window.location.href.match(/p\/([a-zA-Z0-9]+)/);
        return match ? match[1] : null;
    }

    extractMyntraProductId() {
        const match = window.location.href.match(/\/([0-9]+)\/)/);
        return match ? match[1] : null;
    }

    setupListeners() {
        // Listen for messages from popup
        chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
            if (request.action === 'getProduct') {
                sendResponse({ product: this.product });
            } else if (request.action === 'addCurrentToWatchlist') {
                // Add current product to watchlist
                chrome.runtime.sendMessage({
                    action: 'addToWatchlist',
                    product: this.product
                });
            }
        });
    }
}

// Initialize detector
const detector = new ProductDetector();
console.log('🛍️ Pater content script loaded for:', detector.platform);
