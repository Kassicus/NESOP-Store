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
    document.getElementById('app').innerHTML = `
      <header class="store-header">
        <div class="container">
          <h1 class="store-title">NESOP Swag Store</h1>
          <div class="user-info">
            <span>Welcome, ${username}! Balance: ${balance} ESOP Bucks</span>
            ${username === 'admin' ? '<a href="admin.html" class="admin-link">Admin Panel</a>' : ''}
            <a href="cart.html" class="cart-link" title="View Cart">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" class="cart-icon" width="28" height="28"><defs><style>.cls-1{fill:#231f20}</style></defs><g id="cart"><path class="cls-1" d="M29.46 10.14A2.94 2.94 0 0 0 27.1 9H10.22L8.76 6.35A2.67 2.67 0 0 0 6.41 5H3a1 1 0 0 0 0 2h3.41a.68.68 0 0 1 .6.31l1.65 3 .86 9.32a3.84 3.84 0 0 0 4 3.38h10.37a3.92 3.92 0 0 0 3.85-2.78l2.17-7.82a2.58 2.58 0 0 0-.45-2.27zM28 11.86l-2.17 7.83A1.93 1.93 0 0 1 23.89 21H13.48a1.89 1.89 0 0 1-2-1.56L10.73 11H27.1a1 1 0 0 1 .77.35.59.59 0 0 1 .13.51z"/><circle class="cls-1" cx="14" cy="26" r="2"/><circle class="cls-1" cx="24" cy="26" r="2"/></g></svg>
              <span id="cart-count-badge" class="cart-count-badge">0</span>
            </a>
            <button id="logout-btn" class="logout-btn">Logout</button>
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
  container.innerHTML = items.map((item, idx) => `
    <div class="product-card">
      <img src="${item.image || 'assets/images/placeholder.png'}" alt="${item.item}" class="product-img" onerror="this.onerror=null;this.src='assets/images/placeholder.png';" />
      <div class="product-info">
        <h3 class="product-name">${item.item}</h3>
        <p class="product-desc">${item.description}</p>
        <div class="product-bottom">
          <span class="product-price">${item.price} ESOP Bucks</span>
          <button class="add-cart-btn" data-idx="${idx}">Add to Cart</button>
        </div>
      </div>
    </div>
  `).join('');

  // Add event listeners for Add to Cart buttons
  const buttons = container.querySelectorAll('.add-cart-btn');
  buttons.forEach(btn => {
    btn.disabled = false;
    btn.addEventListener('click', function() {
      const idx = parseInt(this.getAttribute('data-idx'));
      const cart = getCart();
      cart.push(items[idx]);
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