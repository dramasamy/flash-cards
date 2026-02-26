// Flash Cards Video Creator - Main JavaScript

class FlashCardCreator {
    constructor() {
        this.sessionId = null;
        this.selections = {};
        this.totalItems = 0;
        this.init();
    }

    init() {
        this.bindEvents();
        this.initializeTooltips();
    }

    bindEvents() {
        // Form submission
        const form = document.getElementById('flashcardForm');
        if (form) {
            form.addEventListener('submit', (e) => this.handleFormSubmit(e));
        }

        // Image selection
        document.addEventListener('click', (e) => {
            if (e.target.closest('.image-option')) {
                this.handleImageSelection(e.target.closest('.image-option'));
            }
        });

        // Keyboard navigation for images
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                const focusedElement = document.activeElement;
                if (focusedElement.matches('.image-option')) {
                    e.preventDefault();
                    this.handleImageSelection(focusedElement);
                }
            }
        });

        // Auto-save selections
        window.addEventListener('beforeunload', () => {
            this.saveSelections();
        });
    }

    initializeTooltips() {
        // Initialize Bootstrap tooltips if available
        if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
            const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
            tooltipTriggerList.map(function (tooltipTriggerEl) {
                return new bootstrap.Tooltip(tooltipTriggerEl);
            });
        }
    }

    async handleFormSubmit(e) {
        e.preventDefault();
        
        const formData = new FormData(e.target);
        const prompt = formData.get('prompt') || document.getElementById('prompt').value;
        const maxItems = parseInt(formData.get('maxItems') || document.getElementById('maxItems').value);

        if (!prompt.trim()) {
            this.showAlert('Please enter a topic or category.', 'warning');
            return;
        }

        this.showLoading('Generating flashcard items...');
        
        try {
            // Step 1: Create flashcards
            const response = await this.apiCall('/create_flashcards', {
                method: 'POST',
                body: JSON.stringify({
                    prompt: prompt,
                    max_items: maxItems
                })
            });

            if (response.error) {
                throw new Error(response.error);
            }

            this.sessionId = response.session_id;
            this.updateProgress(25, 'Items generated! Fetching images...');

            // Step 2: Fetch images
            const imagesResponse = await this.apiCall(`/fetch_images/${this.sessionId}`);
            
            if (imagesResponse.error) {
                throw new Error(imagesResponse.error);
            }

            this.updateProgress(50, 'Images ready! Redirecting...');
            
            // Redirect to image selection
            setTimeout(() => {
                window.location.href = `/select_images?session_id=${this.sessionId}`;
            }, 1000);

        } catch (error) {
            this.hideLoading();
            this.showAlert(`Error: ${error.message}`, 'danger');
        }
    }

    handleImageSelection(imageElement) {
        const item = imageElement.dataset.item;
        const imageId = imageElement.dataset.imageId;

        // Remove selection from other images for this item
        document.querySelectorAll(`[data-item="${item}"]`).forEach(opt => {
            opt.classList.remove('selected');
            opt.setAttribute('aria-selected', 'false');
        });

        // Select this image
        imageElement.classList.add('selected');
        imageElement.setAttribute('aria-selected', 'true');

        // Store selection (get image data from global variable if available)
        if (window.imageData && window.imageData[item]) {
            this.selections[item] = window.imageData[item].find(img => img.id == imageId);
        }

        this.updateSelectionCounter();
        this.saveSelectionToStorage();

        // Provide visual feedback
        this.showToast(`Selected image for "${item}"`, 'success');
    }

    updateSelectionCounter() {
        const count = Object.keys(this.selections).length;
        const counterElement = document.getElementById('selectionCount');
        
        if (counterElement) {
            counterElement.textContent = count;
        }

        // Update proceed button
        const proceedBtn = document.getElementById('proceedBtn');
        if (proceedBtn) {
            if (count > 0) {
                proceedBtn.disabled = false;
                proceedBtn.classList.remove('btn-secondary');
                proceedBtn.classList.add('btn-success');
            } else {
                proceedBtn.disabled = true;
                proceedBtn.classList.remove('btn-success');
                proceedBtn.classList.add('btn-secondary');
            }
        }
    }

    async proceedToVideoCreation() {
        if (Object.keys(this.selections).length === 0) {
            this.showAlert('Please select at least one image before proceeding.', 'warning');
            return;
        }

        this.showVideoCreationProgress();

        try {
            // Step 1: Save selections
            this.updateVideoStep('save', 'active');
            await this.apiCall('/save_selections', {
                method: 'POST',
                body: JSON.stringify({
                    session_id: this.sessionId,
                    selections: this.selections
                })
            });
            this.updateVideoStep('save', 'complete');

            // Step 2: Generate audio
            this.updateVideoStep('audio', 'active');
            const audioResponse = await this.apiCall(`/generate_audio/${this.sessionId}`);
            
            if (audioResponse.error) {
                throw new Error(audioResponse.error);
            }
            this.updateVideoStep('audio', 'complete');

            // Step 3: Create video
            this.updateVideoStep('video', 'active');
            const videoResponse = await this.apiCall(`/create_video/${this.sessionId}`);
            
            if (videoResponse.error) {
                throw new Error(videoResponse.error);
            }
            this.updateVideoStep('video', 'complete');

            // Step 4: Complete
            this.updateVideoStep('complete', 'complete');
            
            // Redirect to download
            setTimeout(() => {
                window.location.href = `/download_video/${this.sessionId}`;
            }, 2000);

        } catch (error) {
            this.hideVideoCreationProgress();
            this.showAlert(`Error creating video: ${error.message}`, 'danger');
        }
    }

    async apiCall(url, options = {}) {
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
            }
        };

        const response = await fetch(url, { ...defaultOptions, ...options });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    }

    showLoading(message = 'Loading...') {
        const loadingElement = document.querySelector('.loading-spinner');
        const formElement = document.getElementById('flashcardForm');
        
        if (loadingElement && formElement) {
            loadingElement.style.display = 'block';
            formElement.style.display = 'none';
            
            const loadingText = loadingElement.querySelector('p');
            if (loadingText) {
                loadingText.textContent = message;
            }
        }
    }

    hideLoading() {
        const loadingElement = document.querySelector('.loading-spinner');
        const formElement = document.getElementById('flashcardForm');
        
        if (loadingElement && formElement) {
            loadingElement.style.display = 'none';
            formElement.style.display = 'block';
        }
    }

    updateProgress(percent, text) {
        const progressContainer = document.querySelector('.progress-container');
        const progressBar = document.querySelector('.progress-bar');
        const progressText = document.getElementById('progressText');

        if (progressContainer) {
            progressContainer.style.display = 'block';
        }
        
        if (progressBar) {
            progressBar.style.width = percent + '%';
            progressBar.setAttribute('aria-valuenow', percent);
        }
        
        if (progressText) {
            progressText.textContent = text;
        }
    }

    showVideoCreationProgress() {
        const overlay = document.getElementById('loadingOverlay');
        if (overlay) {
            overlay.style.display = 'block';
        }
    }

    hideVideoCreationProgress() {
        const overlay = document.getElementById('loadingOverlay');
        if (overlay) {
            overlay.style.display = 'none';
        }
    }

    updateVideoStep(stepId, status) {
        const step = document.getElementById(`step-${stepId}`);
        if (step) {
            step.classList.remove('step-pending', 'step-active', 'step-complete');
            step.classList.add(`step-${status}`);
        }
    }

    saveSelectionToStorage() {
        if (this.sessionId) {
            localStorage.setItem(`selections_${this.sessionId}`, JSON.stringify(this.selections));
        }
    }

    loadSelectionFromStorage() {
        if (this.sessionId) {
            const saved = localStorage.getItem(`selections_${this.sessionId}`);
            if (saved) {
                this.selections = JSON.parse(saved);
                this.restoreSelections();
            }
        }
    }

    restoreSelections() {
        Object.keys(this.selections).forEach(item => {
            const imageId = this.selections[item].id;
            const imageElement = document.querySelector(`[data-item="${item}"][data-image-id="${imageId}"]`);
            if (imageElement) {
                imageElement.classList.add('selected');
                imageElement.setAttribute('aria-selected', 'true');
            }
        });
        this.updateSelectionCounter();
    }

    showAlert(message, type = 'info') {
        // Create Bootstrap alert
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        // Insert at top of container
        const container = document.querySelector('.container');
        if (container) {
            container.insertBefore(alertDiv, container.firstChild);
            
            // Auto-remove after 5 seconds
            setTimeout(() => {
                alertDiv.remove();
            }, 5000);
        }
    }

    showToast(message, type = 'info') {
        // Simple toast notification
        const toast = document.createElement('div');
        toast.className = `toast-notification toast-${type}`;
        toast.textContent = message;
        toast.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: ${type === 'success' ? '#28a745' : '#17a2b8'};
            color: white;
            padding: 1rem;
            border-radius: 5px;
            z-index: 9999;
            opacity: 0;
            transition: opacity 0.3s ease;
        `;

        document.body.appendChild(toast);
        
        // Fade in
        setTimeout(() => {
            toast.style.opacity = '1';
        }, 100);

        // Auto-remove
        setTimeout(() => {
            toast.style.opacity = '0';
            setTimeout(() => {
                toast.remove();
            }, 300);
        }, 2000);
    }

    // Utility methods
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    async saveSelections() {
        if (this.sessionId && Object.keys(this.selections).length > 0) {
            try {
                await this.apiCall('/save_selections', {
                    method: 'POST',
                    body: JSON.stringify({
                        session_id: this.sessionId,
                        selections: this.selections
                    })
                });
            } catch (error) {
                console.warn('Failed to save selections:', error);
            }
        }
    }
}

// Initialize the application
document.addEventListener('DOMContentLoaded', () => {
    window.flashCardCreator = new FlashCardCreator();
    
    // Make proceedToVideoCreation available globally for template
    window.proceedToVideoCreation = () => {
        window.flashCardCreator.proceedToVideoCreation();
    };
    
    // Load session ID from URL if available
    const urlParams = new URLSearchParams(window.location.search);
    const sessionId = urlParams.get('session_id');
    if (sessionId) {
        window.flashCardCreator.sessionId = sessionId;
        window.flashCardCreator.loadSelectionFromStorage();
    }
});

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = FlashCardCreator;
}
