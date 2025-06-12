// Handles login, logout, and session management
// Refactored for API-based authentication

let users = [];

function showLoginForm() {
  document.getElementById('app').innerHTML = `
    <div class="login-container">
      <h2 style="text-align:center;">NESOP Store</h2>
      <form id="login-form" style="display:flex;flex-direction:column;align-items:center;">
        <input type="text" id="username" placeholder="Username" required style="margin-bottom:0.7em;width:85%;" />
        <input type="password" id="password" placeholder="Password" required style="margin-bottom:0.7em;width:85%;" />
        <button type="submit" class="login-btn" style="margin-bottom:0.7em;width:85%;">Login</button>
        <div id="login-error" style="color:red;margin-top:8px;text-align:center;"></div>
      </form>
      <div style="text-align:center;margin-top:1.5em;">
        <a href="register.html" style="color:#1976d2;text-decoration:none;font-size:1.05em;">Register Here</a>
      </div>
    </div>
  `;
  document.getElementById('login-form').onsubmit = function(e) {
    e.preventDefault();
    const username = document.getElementById('username').value.trim();
    const password = document.getElementById('password').value;
    fetch('/api/users')
      .then(res => res.json())
      .then(data => {
        users = data.users || [];
        const user = users.find(u => u.username === username && u.password === password);
        if (user) {
          localStorage.setItem('nesop_user', username);
          localStorage.setItem('nesop_user_admin', user.is_admin ? 'true' : 'false');
          window.location.reload();
        } else {
          document.getElementById('login-error').textContent = 'Invalid username or password.';
        }
      })
      .catch(() => {
        document.getElementById('login-error').textContent = 'Failed to contact server.';
      });
  };
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