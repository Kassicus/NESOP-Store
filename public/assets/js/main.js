// Main JavaScript Module
const App = {
    // Initialize the application
    init() {
        this.setupEventListeners();
        this.checkAuth();
    },

    // Set up global event listeners
    setupEventListeners() {
        // Add any global event listeners here
    },

    // Check authentication status and update UI
    checkAuth() {
        if (Auth.isLoggedIn()) {
            const user = Auth.getUser();
            // Update UI elements that depend on user data
            this.updateUserUI(user);
        }
    },

    // Update UI elements with user data
    updateUserUI(user) {
        // Add any user-specific UI updates here
    },

    // Handle API errors
    handleApiError(error) {
        console.error('API Error:', error);
        Auth.showFlashMessage('An error occurred. Please try again.', 'error');
    }
};

// Initialize the application when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    App.init();
}); 