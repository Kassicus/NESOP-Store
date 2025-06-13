// Handles loading items, displaying storefront, and adding to cart
// Refactored for API-based data access

function getCart() {
  return JSON.parse(localStorage.getItem('nesop_cart') || '[]');
}

function setCart(cart) {
  localStorage.setItem('nesop_cart', JSON.stringify(cart));
  updateCartCount();
}

function updateCartCount() {
  const cart = getCart();
  const badge = document.getElementById('cart-count-badge');
  if (badge) {
    badge.textContent = cart.length;
    badge.style.display = cart.length > 0 ? 'inline-block' : 'none';
  }
}

// Utility to capitalize the first letter of a string
function capitalizeFirstLetter(str) {
  if (!str) return '';
  return str.charAt(0).toUpperCase() + str.slice(1);
}

function showStore(username) {
  // Fetch both items and user balance from API
  Promise.all([
    fetch('/api/items').then(res => res.json()),
    fetch('/api/users').then(res => res.json())
  ]).then(([itemsData, usersData]) => {
    const items = itemsData.items || [];
    const users = usersData.users || [];
    const user = users.find(u => u.username === username);
    const balance = user ? user.balance : '0';
    const isAdmin = user && user.is_admin === 1;
    
    // Store the admin status in localStorage
    localStorage.setItem('nesop_user_admin', isAdmin ? 'true' : 'false');

    // Center the user info and style username
    document.getElementById('app').innerHTML = `
      <header class="store-header">
        <div class="container">
          <div style="display: flex; justify-content: center; align-items: center; width: 60px; height: 60px; background-color: #fff; border-radius: 50%; margin: 0; padding: 0;">
            <img src="assets/images/nesop-logo.png" alt="NESOP Logo" class="nesop-logo" style="width: 40px; height: 40px; margin: 0; padding: 0;">
          </div>
          <div class="user-info" style="display: flex; justify-content: center; align-items: center; flex-direction: row; margin-top: 0.5rem; margin-bottom: 0.5rem; width: 100%;">
            <div style="display: flex; flex-direction: column; align-items: flex-start; flex: 1; margin-left: 2rem;">
              <span style="font-size:1.25em; margin-left: 0; padding-left: 0;">Welcome <b style="text-transform:capitalize;">${capitalizeFirstLetter(username)}</b>!</span>
              <span style="font-size:0.98em; color:#fff; margin-top:0.2em;">Balance: € ${balance}</span>
            </div>
            <div style="display: flex; align-items: center; gap: 0.5rem;">
              <a href="cart.html" class="cart-link" title="View Cart">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" class="cart-icon" width="32" height="32"><defs><style>.cls-1{fill:#231f20}</style></defs><g id="cart"><path class="cls-1" d="M29.46 10.14A2.94 2.94 0 0 0 27.1 9H10.22L8.76 6.35A2.67 2.67 0 0 0 6.41 5H3a1 1 0 0 0 0 2h3.41a.68.68 0 0 1 .6.31l1.65 3 .86 9.32a3.84 3.84 0 0 0 4 3.38h10.37a3.92 3.92 0 0 0 3.85-2.78l2.17-7.82a2.58 2.58 0 0 0-.45-2.27zM28 11.86l-2.17 7.83A1.93 1.93 0 0 1 23.89 21H13.48a1.89 1.89 0 0 1-2-1.56L10.73 11H27.1a1 1 0 0 1 .77.35.59.59 0 0 1 .13.51z"/><circle class="cls-1" cx="14" cy="26" r="2"/><circle class="cls-1" cx="24" cy="26" r="2"/></g></svg>
                <span id="cart-count-badge" class="cart-count-badge">0</span>
              </a>
              ${isAdmin ? '<button onclick="window.location.href=\'admin.html\'" class="admin-link logout-btn">Admin Panel</button>' : ''}
              <button id="logout-btn" class="logout-btn">Logout</button>
            </div>
          </div>
        </div>
      </header>
      <main>
        <div class="container">
          <div class="product-grid" id="store-items"></div>
        </div>
      </main>
    `;
    document.getElementById('logout-btn').onclick = function() {
      window.nesopLogout();
    };
    renderItems(items);
    updateCartCount();
  }).catch(err => {
    document.getElementById('app').innerHTML = '<p style="color:red;">Failed to load store data.</p>';
    console.error('Error loading store data:', err);
  });
}

function renderItems(items) {
  const container = document.getElementById('store-items');
  if (!container) return;
  // Filter out unlisted items
  const visibleItems = items.filter(item => !item.unlisted);
  container.innerHTML = visibleItems.map((item, idx) => `
    <div class="product-card">
      <img src="${item.image || 'assets/images/placeholder.png'}" alt="${item.item}" class="product-img${item.sold_out ? ' sold-out-img' : ''}" onerror="this.onerror=null;this.src='assets/images/placeholder.png';" />
      <div class="product-info">
        <h3 class="product-name">${item.item}</h3>
        <p class="product-desc">${item.description}</p>
        <div class="product-bottom">
          <span class="product-price">€ ${item.price}</span>
          <button class="add-cart-btn${item.sold_out ? ' sold-out-btn' : ''}" data-idx="${idx}" ${item.sold_out ? 'disabled' : ''}>${item.sold_out ? 'Sold Out' : 'Add to Cart'}</button>
        </div>
      </div>
    </div>
  `).join('');

  // Add event listeners for Add to Cart buttons
  const buttons = container.querySelectorAll('.add-cart-btn');
  buttons.forEach(btn => {
    // If button is disabled (sold out), skip adding event listener
    if (btn.disabled) return;
    btn.addEventListener('click', function() {
      const idx = parseInt(this.getAttribute('data-idx'));
      const cart = getCart();
      cart.push(visibleItems[idx]);
      setCart(cart);
      updateCartCount();
      this.textContent = 'Added!';
      this.disabled = true;
      setTimeout(() => {
        this.textContent = 'Add to Cart';
        this.disabled = false;
      }, 1000);
    });
  });
}

// Add styles for sold out button and image
(function() {
  const style = document.createElement('style');
  style.innerHTML = `
    .sold-out-btn {
      background: #e57373 !important;
      color: #fff !important;
      border: none;
      cursor: not-allowed;
    }
    .sold-out-btn:disabled {
      background: #e57373 !important;
      color: #fff !important;
      opacity: 1 !important;
    }
    .sold-out-img {
      filter: grayscale(1) brightness(0.85);
    }
  `;
  document.head.appendChild(style);
})(); 