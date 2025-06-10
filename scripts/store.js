// Handles loading items, displaying storefront, and adding to cart
// Placeholder for storefront logic 

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
  // Fetch both items and user balance
  Promise.all([
    fetch('data/items.csv').then(res => res.text()),
    fetch('data/users.csv').then(res => res.text())
  ]).then(([itemsCsv, usersCsv]) => {
    const items = window.parseCSV(itemsCsv);
    const users = window.parseCSV(usersCsv);
    const user = users.find(u => u.username === username);
    const balance = user ? user.balance : '0';
    document.getElementById('app').innerHTML = `
      <header class="store-header">
        <div class="container">
          <h1 class="store-title">NESOP Swag Store</h1>
          <div class="user-info">
            <span>Welcome, ${username} &mdash; <b>${balance} ESOP Bucks</b></span>
            ${username === 'admin' ? '<a href="admin.html" class="admin-link">Admin Panel</a>' : ''}
            <a href="cart.html" class="cart-link" title="View Cart">
              <svg class="cart-icon" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#1976d2" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="9" cy="21" r="1"/><circle cx="20" cy="21" r="1"/><path d="M1 1h2l3.6 7.59a2 2 0 0 0 1.7 1.18h9.72a2 2 0 0 0 1.98-1.7l1.38-7.07H6.16"/></svg>
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
      <img src="${item.image}" alt="${item.item}" class="product-img" />
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