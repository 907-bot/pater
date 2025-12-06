// storage.js - Chrome storage wrapper

class Storage {
    static async get(key) {
        return new Promise((resolve) => {
            chrome.storage.sync.get(key, (result) => {
                resolve(result[key]);
            });
        });
    }

    static async set(key, value) {
        return new Promise((resolve) => {
            chrome.storage.sync.set({ [key]: value }, () => {
                resolve();
            });
        });
    }

    static async remove(key) {
        return new Promise((resolve) => {
            chrome.storage.sync.remove(key, () => {
                resolve();
            });
        });
    }

    static async clear() {
        return new Promise((resolve) => {
            chrome.storage.sync.clear(() => {
                resolve();
            });
        });
    }

    static async getAll() {
        return new Promise((resolve) => {
            chrome.storage.sync.get(null, (items) => {
                resolve(items);
            });
        });
    }

    // Local storage methods
    static getLocal(key) {
        const value = localStorage.getItem(key);
        return value ? JSON.parse(value) : null;
    }

    static setLocal(key, value) {
        localStorage.setItem(key, JSON.stringify(value));
    }

    static removeLocal(key) {
        localStorage.removeItem(key);
    }

    static clearLocal() {
        localStorage.clear();
    }
}
