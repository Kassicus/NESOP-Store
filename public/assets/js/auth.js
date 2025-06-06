// Authentication Module
const Auth = {
    // Check if user is logged in
    isLoggedIn() {
        return localStorage.getItem('user') !== null;
    },

    // Get current user data
    getUser() {
        const user = localStorage.getItem('user');
        return user ? JSON.parse(user) : null;
    },

    // Show/hide navigation links based on auth status
    updateNavigation() {
        const dashboardLink = document.getElementById('dashboardLink');
        const cartLink = document.getElementById('cartLink');
        const logoutLink = document.getElementById('logoutLink');
        const loginLink = document.getElementById('loginLink');

        if (this.isLoggedIn()) {
            dashboardLink.style.display = 'inline-block';
            cartLink.style.display = 'inline-block';
            logoutLink.style.display = 'inline-block';
            loginLink.style.display = 'none';
        } else {
            dashboardLink.style.display = 'none';
            cartLink.style.display = 'none';
            logoutLink.style.display = 'none';
            loginLink.style.display = 'inline-block';
        }
    },

    // Show flash message
    showFlashMessage(message, type = 'info') {
        const flashMessage = document.getElementById('flashMessage');
        if (flashMessage) {
            flashMessage.textContent = message;
            flashMessage.className = `flash-message ${type}`;
            flashMessage.style.display = 'block';
            
            // Hide message after 5 seconds
            setTimeout(() => {
                flashMessage.style.display = 'none';
            }, 5000);
        }
    },

    // Handle login form submission
    async handleLogin(event) {
        event.preventDefault();
        
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;

        try {
            const response = await fetch('/api/auth/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ username, password })
            });

            const data = await response.json();

            if (response.ok) {
                // Store user data
                localStorage.setItem('user', JSON.stringify(data.user));
                this.showFlashMessage('Login successful!', 'success');
                
                // Redirect to dashboard
                window.location.href = '/dashboard.html';
            } else {
                this.showFlashMessage(data.message || 'Login failed', 'error');
            }
        } catch (error) {
            console.error('Login error:', error);
            this.showFlashMessage('An error occurred. Please try again.', 'error');
        }
    },

    // Handle logout
    handleLogout() {
        localStorage.removeItem('user');
        this.showFlashMessage('You have been logged out.', 'success');
        window.location.href = '/index.html';
    }
};

// Initialize auth functionality
document.addEventListener('DOMContentLoaded', () => {
    // Update navigation based on auth status
    Auth.updateNavigation();

    // Set up login form handler
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', (e) => Auth.handleLogin(e));
    }

    // Set up logout handler
    const logoutLink = document.getElementById('logoutLink');
    if (logoutLink) {
        logoutLink.addEventListener('click', (e) => {
            e.preventDefault();
            Auth.handleLogout();
        });
    }

    // Set current year in footer
    const currentYear = document.getElementById('currentYear');
    if (currentYear) {
        currentYear.textContent = new Date().getFullYear();
    }
}); 