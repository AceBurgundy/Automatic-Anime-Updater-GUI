import { showToast } from '../../../toast/scripts/toast__service.js';

/**
 * Copies the provided code text to clipboard and displays a feedback toast.
 * @param {string} codeText - Code content string to copy.
 * @returns {Promise<void>} Resolves when copy operation finishes.
 */
export async function copyCodeToClipboard(codeText) {
    if (!codeText) {
        return;
    }

    try {
        if (navigator.clipboard && typeof navigator.clipboard.writeText === 'function') {
            await navigator.clipboard.writeText(codeText);
        } else {
            /** @type {HTMLTextAreaElement} */
            const temporaryTextArea = document.createElement('textarea');
            temporaryTextArea.value = codeText;
            temporaryTextArea.style.position = 'fixed';
            temporaryTextArea.style.left = '-999999px';
            temporaryTextArea.style.top = '-999999px';
            document.body.appendChild(temporaryTextArea);
            temporaryTextArea.focus();
            temporaryTextArea.select();
            document.execCommand('copy');
            document.body.removeChild(temporaryTextArea);
        }

        showToast('Code copied to clipboard!');
    } catch (error) {
        console.error('Failed to copy code to clipboard:', error);
        showToast('Failed to copy code');
    }
}
