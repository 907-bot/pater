// logger.js - Logging utility

class Logger {
    static LOG_LEVEL = {
        DEBUG: 0,
        INFO: 1,
        WARN: 2,
        ERROR: 3
    };

    static currentLevel = Logger.LOG_LEVEL.INFO;

    static debug(message, data = null) {
        if (this.currentLevel <= this.LOG_LEVEL.DEBUG) {
            console.log(`[DEBUG] ${message}`, data);
        }
    }

    static info(message, data = null) {
        if (this.currentLevel <= this.LOG_LEVEL.INFO) {
            console.log(`[INFO] ${message}`, data);
        }
    }

    static warn(message, data = null) {
        if (this.currentLevel <= this.LOG_LEVEL.WARN) {
            console.warn(`[WARN] ${message}`, data);
        }
    }

    static error(message, error = null) {
        if (this.currentLevel <= this.LOG_LEVEL.ERROR) {
            console.error(`[ERROR] ${message}`, error);
        }
    }

    static setLevel(level) {
        this.currentLevel = level;
    }

    static enableDebug() {
        this.currentLevel = this.LOG_LEVEL.DEBUG;
    }

    static disableDebug() {
        this.currentLevel = this.LOG_LEVEL.INFO;
    }
}

// Set to INFO by default
Logger.setLevel(Logger.LOG_LEVEL.INFO);
