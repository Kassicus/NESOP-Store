// Handles login, logout, and session management
// Placeholder for authentication logic 

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
    const user = users.find(u => u.username === username && u.password === password);
    if (user) {
      localStorage.setItem('nesop_user', username);
      window.location.reload();
    } else {
      document.getElementById('login-error').textContent = 'Invalid username or password.';
    }
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
    } else {
      document.getElementById('app').innerHTML = '<p>Welcome, ' + user + '!</p>';
    }
  }
}

function loadUsersAndStart() {
  fetch('data/users.csv')
    .then(res => res.text())
    .then(csv => {
      users = window.parseCSV(csv);
      checkLogin();
    })
    .catch(err => {
      document.getElementById('app').innerHTML = '<p style="color:red;">Failed to load users data.</p>';
      console.error('Error loading users.csv:', err);
    });
}

document.addEventListener('DOMContentLoaded', loadUsersAndStart);

// Export a logout function for use in other scripts
window.nesopLogout = function() {
  localStorage.removeItem('nesop_user');
  window.location.href = 'index.html';
}; 