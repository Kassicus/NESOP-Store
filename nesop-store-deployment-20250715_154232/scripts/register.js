document.getElementById('register-form').onsubmit = async function(e) {
  e.preventDefault();
  const username = document.getElementById('reg-username').value.trim();
  const password = document.getElementById('reg-password').value;
  const errorDiv = document.getElementById('register-error');
  const successDiv = document.getElementById('register-success');
  errorDiv.textContent = '';
  successDiv.textContent = '';
  if (!username || !password) {
    errorDiv.textContent = 'Username and password are required.';
    return;
  }
  try {
    const res = await fetch('/api/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    });
    const data = await res.json();
    if (data.success) {
      successDiv.textContent = 'Registration successful! You can now log in.';
      setTimeout(() => { window.location.href = 'index.html'; }, 1500);
    } else {
      errorDiv.textContent = data.error || 'Registration failed.';
    }
  } catch (err) {
    errorDiv.textContent = 'Registration failed. Please try again.';
  }
}; 