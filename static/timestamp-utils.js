/**
 * Shared timestamp utilities for both live chat and HTML export
 */

class TimestampUtils {
    /**
     * Generate a formatted timestamp for display
     * @param {Date} date - Optional date object, defaults to current time
     * @returns {string} Formatted timestamp string
     */
    static formatTimestamp(date = new Date()) {
        return date.toLocaleTimeString([], { 
            hour: '2-digit', 
            minute: '2-digit',
            hour12: true 
        });
    }

    /**
     * Generate a full datetime string for HTML export
     * @param {Date} date - Optional date object, defaults to current time
     * @returns {string} Full datetime string
     */
    static formatFullDateTime(date = new Date()) {
        return date.toLocaleString([], {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
            hour12: true
        });
    }

    /**
     * Generate ISO string for data attributes
     * @param {Date} date - Optional date object, defaults to current time
     * @returns {string} ISO datetime string
     */
    static formatISO(date = new Date()) {
        return date.toISOString();
    }

    /**
     * Create a timestamp element for live chat
     * @param {Date} date - Optional date object, defaults to current time
     * @param {string} messageType - 'user' or 'bot' for positioning
     * @returns {string} HTML string for timestamp element
     */
    static createChatTimestamp(date = new Date(), messageType = 'bot') {
        const timestamp = this.formatTimestamp(date);
        const fullDateTime = this.formatFullDateTime(date);
        const isoString = this.formatISO(date);
        
        return `<div class="message-timestamp ${messageType}-timestamp" 
                     title="${fullDateTime}" 
                     data-time="${isoString}">
                    ${timestamp}
                </div>`;
    }

    /**
     * Create a timestamp element for HTML export
     * @param {Date} date - Optional date object, defaults to current time
     * @param {string} messageType - 'user' or 'bot' for positioning
     * @returns {string} HTML string for export timestamp element
     */
    static createExportTimestamp(date = new Date(), messageType = 'bot') {
        const timestamp = this.formatTimestamp(date);
        const fullDateTime = this.formatFullDateTime(date);
        
        return `<div class="message-timestamp ${messageType}-timestamp" 
                     title="${fullDateTime}">
                    ${timestamp}
                </div>`;
    }
}

// For use in HTML export (when window is not available)
if (typeof module !== 'undefined' && module.exports) {
    module.exports = TimestampUtils;
}

// For use in browser
if (typeof window !== 'undefined') {
    window.TimestampUtils = TimestampUtils;
}