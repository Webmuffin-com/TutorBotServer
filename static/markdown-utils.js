/**
 * Shared markdown utilities for both live chat and HTML export
 */

class MarkdownUtils {
    /**
     * Render markdown to HTML using the marked library
     * @param {string} markdown - The markdown text to render
     * @returns {string} Rendered HTML
     */
    static renderMarkdown(markdown) {
        if (typeof marked === 'undefined') {
            console.warn('Marked library not available, falling back to basic HTML escaping');
            return MarkdownUtils.escapeHtml(markdown).replace(/\n/g, '<br>');
        }
        
        try {
            const html = marked.parse(markdown);
            return DOMPurify ? DOMPurify.sanitize(html) : html;
        } catch (error) {
            console.error('Error rendering markdown:', error);
            return MarkdownUtils.escapeHtml(markdown).replace(/\n/g, '<br>');
        }
    }

    /**
     * Escape HTML characters
     * @param {string} text - Text to escape
     * @returns {string} Escaped text
     */
    static escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * Render all markdown elements on a page
     * @param {string} selector - CSS selector for elements containing markdown
     */
    static renderAllMarkdown(selector = '.rendered-markdown[data-markdown]') {
        const elements = document.querySelectorAll(selector);
        elements.forEach(element => {
            const markdown = element.getAttribute('data-markdown');
            if (markdown) {
                // Decode HTML entities from the data attribute
                const decodedMarkdown = MarkdownUtils.decodeHtmlEntities(markdown);
                element.innerHTML = MarkdownUtils.renderMarkdown(decodedMarkdown);
            }
        });
    }

    /**
     * Decode HTML entities
     * @param {string} text - Text with HTML entities
     * @returns {string} Decoded text
     */
    static decodeHtmlEntities(text) {
        const textarea = document.createElement('textarea');
        textarea.innerHTML = text;
        return textarea.value;
    }

    /**
     * Initialize markdown rendering when DOM is ready
     */
    static initialize() {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => {
                MarkdownUtils.renderAllMarkdown();
            });
        } else {
            MarkdownUtils.renderAllMarkdown();
        }
    }

    /**
     * Re-render markdown for a specific element
     * @param {HTMLElement} element - Element containing markdown
     */
    static renderElement(element) {
        const markdown = element.getAttribute('data-markdown');
        if (markdown) {
            const decodedMarkdown = MarkdownUtils.decodeHtmlEntities(markdown);
            element.innerHTML = MarkdownUtils.renderMarkdown(decodedMarkdown);
        }
    }

    /**
     * Format markdown content (for backward compatibility with existing code)
     * @param {string} markdown - Markdown text
     * @returns {string} Rendered HTML
     */
    static formatMarkdown(markdown) {
        return MarkdownUtils.renderMarkdown(markdown);
    }
}

// Auto-initialize when script loads
MarkdownUtils.initialize();

// For use in HTML export (when window is not available in some contexts)
if (typeof module !== 'undefined' && module.exports) {
    module.exports = MarkdownUtils;
}

// For use in browser
if (typeof window !== 'undefined') {
    window.MarkdownUtils = MarkdownUtils;
}