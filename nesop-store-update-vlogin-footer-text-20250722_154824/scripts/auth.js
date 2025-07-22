// Handles login, logout, and session management
// Refactored for API-based authentication

let users = [];

function showLoginForm() {
  document.getElementById('app').innerHTML = `
    <div style="position: fixed; top: 1rem; right: 1rem; z-index: 1000;">
      <button 
        type="button" 
        data-theme-toggle 
        aria-label="Change theme"
        class="theme-toggle-btn register-page"
      >
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path></svg>
      </button>
    </div>
    <div class="login-page-background">
      <div class="login-splash-image">
        <img src="assets/resources/nesop_splash.jpg" alt="NESOP Store" class="splash-image" />
      </div>
      <div class="login-container">
        <h2 style="text-align:center;">Login</h2>
        <form id="login-form" style="display:flex;flex-direction:column;align-items:center;">
          <input type="text" id="username" placeholder="Username" required style="margin-bottom:0.7em;width:85%;" />
          <input type="password" id="password" placeholder="Password" required style="margin-bottom:0.7em;width:85%;" />
          <button type="submit" class="login-btn" style="margin-bottom:0.7em;width:85%;">Login</button>
          <div id="login-error" style="color:red;margin-top:8px;text-align:center;"></div>
        </form>
        <div class="login-footer" style="text-align:center;margin-top:2rem;color:#666;font-size:0.9rem;opacity:0.8;">
          Made with ❤️ by the ESOP Committee
        </div>
      </div>
    </div>
  `;
  document.getElementById('login-form').onsubmit = function(e) {
    e.preventDefault();
    const username = document.getElementById('username').value.trim();
    const password = document.getElementById('password').value;
    
    // Clear previous error
    document.getElementById('login-error').textContent = '';
    
    // Show loading state
    const loginBtn = document.querySelector('.login-btn');
    const originalText = loginBtn.textContent;
    loginBtn.textContent = 'Logging in...';
    loginBtn.disabled = true;
    
    fetch('/api/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        username: username,
        password: password
      })
    })
    .then(res => res.json())
    .then(data => {
      if (data.success) {
        // Store user information
        localStorage.setItem('nesop_user', data.user.username);
        localStorage.setItem('nesop_user_admin', data.user.is_admin ? 'true' : 'false');
        localStorage.setItem('nesop_user_type', data.user.user_type);
        localStorage.setItem('nesop_auth_method', data.auth_method);
        
        // Store display name if available
        if (data.user.display_name) {
          localStorage.setItem('nesop_user_display_name', data.user.display_name);
        }
        
        console.log(`Login successful via ${data.auth_method} authentication`);
        window.location.reload();
      } else {
        document.getElementById('login-error').textContent = data.error || 'Login failed.';
      }
    })
    .catch((error) => {
      console.error('Login error:', error);
      document.getElementById('login-error').textContent = 'Failed to contact server.';
    })
    .finally(() => {
      // Reset button state
      loginBtn.textContent = originalText;
      loginBtn.disabled = false;
    });
  };
  
  // Set up theme toggle
  setTimeout(setupThemeToggle, 100);
}

function checkLogin() {
  const user = localStorage.getItem('nesop_user');
  if (!user) {
    showLoginForm();
  } else {
    // User is logged in, show store
    if (typeof showStore === 'function') {
      showStore(user);
      
      // Check if user is admin and show admin panel link if so
      const isAdmin = localStorage.getItem('nesop_user_admin') === 'true';
      const adminPanelLink = document.getElementById('admin-panel-link');
      if (adminPanelLink) {
        if (isAdmin) {
          adminPanelLink.innerHTML = '<a href="admin.html" class="admin-link">Admin Panel</a>';
        } else {
          adminPanelLink.innerHTML = '';
        }
      }
    } else {
      document.getElementById('app').innerHTML = '<p>Welcome, ' + user + '!</p>';
    }
  }
}

function loadUsersAndStart() {
  // No longer needed, just check login
  checkLogin();
}

document.addEventListener('DOMContentLoaded', loadUsersAndStart);

// Export a logout function for use in other scripts
window.nesopLogout = function() {
  localStorage.removeItem('nesop_user');
  localStorage.removeItem('nesop_user_admin');
  window.location.href = 'index.html';
}; 