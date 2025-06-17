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

// --- Product Modal Logic ---
let productModal = null;

function createProductModal() {
  if (productModal) return productModal;
  productModal = document.createElement('div');
  productModal.id = 'product-modal';
  productModal.style.display = 'none';
  productModal.innerHTML = `
    <div class="modal-backdrop"></div>
    <div class="modal-content">
      <button class="modal-close" id="modal-close-btn">&times;</button>
      <div id="modal-product-content"></div>
    </div>
  `;
  document.body.appendChild(productModal);
  // Close modal on backdrop or close button
  productModal.querySelector('.modal-backdrop').onclick = closeProductModal;
  productModal.querySelector('#modal-close-btn').onclick = closeProductModal;
  // Close on Escape
  document.addEventListener('keydown', function(e) {
    if (productModal.style.display === 'block' && e.key === 'Escape') closeProductModal();
  });
  return productModal;
}

function openProductModal(itemName) {
  const modal = createProductModal();
  modal.style.display = 'block';
  document.body.style.overflow = 'hidden';
  // Loading state
  document.getElementById('modal-product-content').innerHTML = '<div class="modal-loading">Loading...</div>';
  // Fetch product details and reviews
  Promise.all([
    fetch(`/api/product/${encodeURIComponent(itemName)}`).then(r => r.json()),
    fetch(`/api/product/${encodeURIComponent(itemName)}/reviews`).then(r => r.json())
  ]).then(([product, reviewsData]) => {
    if (product.error) {
      document.getElementById('modal-product-content').innerHTML = `<div class="modal-error">${product.error}</div>`;
      return;
    }
    const reviews = reviewsData.reviews || [];
    // Modal header styled like store-header
    modal.querySelector('.modal-content').innerHTML = `
      <div class="modal-header">
        <span class="modal-title">${product.item}</span>
        <button class="modal-close" id="modal-close-btn">&times;</button>
      </div>
      <div id="modal-product-content" class="container"></div>
    `;
    modal.querySelector('#modal-close-btn').onclick = closeProductModal;
    // Modal content
    document.getElementById('modal-product-content').innerHTML = `
      <div class="modal-product-main">
        <img src="${product.image || 'assets/images/placeholder.png'}" alt="${product.item}" class="modal-product-img" onerror="this.onerror=null;this.src='assets/images/placeholder.png';" />
        <div class="modal-product-info">
          <h2 class="product-name" style="margin-top:0;">${product.item}</h2>
          <p class="product-desc">${product.description}</p>
          <div class="modal-product-price">€ ${product.price}</div>
          <button id="modal-add-cart-btn" class="add-cart-btn${product.sold_out ? ' sold-out-btn' : ''}" ${product.sold_out ? 'disabled' : ''} style="margin-top:1em;">${product.sold_out ? 'Sold Out' : 'Add to Cart'}</button>
        </div>
      </div>
      <div class="modal-reviews-section">
        <h3 style="color:#1976d2;">Reviews</h3>
        <div id="modal-reviews-list">
          ${reviews.length === 0 ? '<p style="color:#888;">No reviews yet.</p>' : reviews.map(r => `
            <div class="review">
              <div class="review-header">
                <span class="review-user">${r.username ? r.username : 'Anonymous'}</span>
                <span class="review-rating">${'★'.repeat(r.rating)}${'☆'.repeat(5 - r.rating)}</span>
                <span class="review-date">${new Date(r.timestamp).toLocaleString()}</span>
              </div>
              <div class="review-text">${r.review_text}</div>
            </div>
          `).join('')}
        </div>
        <form id="modal-review-form">
          <h4 style="color:#1976d2;">Leave a Review</h4>
          <label>Rating:
            <select name="rating" required>
              <option value="">Select</option>
              <option value="5">5 - Excellent</option>
              <option value="4">4 - Good</option>
              <option value="3">3 - Average</option>
              <option value="2">2 - Poor</option>
              <option value="1">1 - Terrible</option>
            </select>
          </label>
          <label>Review:<br>
            <textarea name="review_text" rows="3" required></textarea>
          </label>
          <input type="text" name="username" placeholder="Your name (optional)" />
          <button type="submit">Submit Review</button>
          <div id="modal-review-error" style="color:#e57373;margin-top:0.5em;"></div>
        </form>
      </div>
    `;
    // Add to Cart button logic
    const addCartBtn = document.getElementById('modal-add-cart-btn');
    if (addCartBtn && !product.sold_out) {
      addCartBtn.onclick = function() {
        const cart = getCart();
        // Prevent duplicates (optional: allow multiple quantities if desired)
        if (!cart.find(i => i.item === product.item)) {
          cart.push(product);
          setCart(cart);
          updateCartCount();
        }
        addCartBtn.textContent = 'Added!';
        addCartBtn.disabled = true;
        setTimeout(() => {
          addCartBtn.textContent = 'Add to Cart';
          addCartBtn.disabled = false;
        }, 1000);
      };
    }
    // Review form submit handler
    document.getElementById('modal-review-form').onsubmit = function(e) {
      e.preventDefault();
      const form = e.target;
      const rating = form.rating.value;
      const review_text = form.review_text.value.trim();
      const username = form.username.value.trim();
      if (!rating || !review_text) {
        document.getElementById('modal-review-error').textContent = 'Rating and review text required.';
        return;
      }
      fetch(`/api/product/${encodeURIComponent(itemName)}/reviews`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ rating, review_text, username })
      }).then(r => r.json()).then(resp => {
        if (!resp.success) {
          document.getElementById('modal-review-error').textContent = resp.error || 'Failed to submit review.';
        } else {
          // Reload reviews
          fetch(`/api/product/${encodeURIComponent(itemName)}/reviews`).then(r => r.json()).then(reviewsData2 => {
            const reviews2 = reviewsData2.reviews || [];
            document.getElementById('modal-reviews-list').innerHTML = reviews2.length === 0 ? '<p style="color:#888;">No reviews yet.</p>' : reviews2.map(r => `
              <div class="review">
                <div class="review-header">
                  <span class="review-user">${r.username ? r.username : 'Anonymous'}</span>
                  <span class="review-rating">${'★'.repeat(r.rating)}${'☆'.repeat(5 - r.rating)}</span>
                  <span class="review-date">${new Date(r.timestamp).toLocaleString()}</span>
                </div>
                <div class="review-text">${r.review_text}</div>
              </div>
            `).join('');
            form.reset();
            document.getElementById('modal-review-error').textContent = '';
          });
        }
      }).catch(() => {
        document.getElementById('modal-review-error').textContent = 'Failed to submit review.';
      });
    };
  }).catch(err => {
    document.getElementById('modal-product-content').innerHTML = `<div class="modal-error">Failed to load product info.</div>`;
    console.error('Error loading product modal:', err);
  });
}

function closeProductModal() {
  if (productModal) {
    productModal.style.display = 'none';
    document.body.style.overflow = '';
  }
}

function renderItems(items) {
  const container = document.getElementById('store-items');
  if (!container) return;
  // Filter out unlisted items
  const visibleItems = items.filter(item => !item.unlisted);
  container.innerHTML = visibleItems.map((item, idx) => `
    <div class="product-card">
      <img src="${item.image || 'assets/images/placeholder.png'}" alt="${item.item}" class="product-img${item.sold_out ? ' sold-out-img' : ''}" onerror="this.onerror=null;this.src='assets/images/placeholder.png';" data-item="${item.item}" style="cursor:pointer;" />
      <div class="product-info">
        <h3 class="product-name" data-item="${item.item}" style="cursor:pointer;">${item.item}</h3>
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

  // Add event listeners for product image and title to open modal
  container.querySelectorAll('.product-img, .product-name').forEach(el => {
    el.addEventListener('click', function() {
      const itemName = this.getAttribute('data-item');
      openProductModal(itemName);
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

// --- Modal Styles ---
(function() {
  const style = document.createElement('style');
  style.innerHTML = `
    #product-modal { position: fixed; z-index: 10000; top: 0; left: 0; width: 100vw; height: 100vh; display: none; }
    #product-modal .modal-backdrop { position: absolute; top: 0; left: 0; width: 100vw; height: 100vh; background: rgba(0,0,0,0.65); }
    #product-modal .modal-content { position: absolute; top: 50%; left: 50%; transform: translate(-50%,-50%); background: #fff; border-radius: 16px; max-width: 700px; width: 95vw; max-height: 90vh; overflow-y: auto; box-shadow: 0 8px 32px rgba(0,0,0,0.25); padding: 2rem 1.5rem 1.5rem 1.5rem; }
    #product-modal .modal-close { position: absolute; top: 1rem; right: 1rem; background: none; border: none; font-size: 2rem; color: #333; cursor: pointer; }
    #modal-product-content .modal-product-main { display: flex; gap: 2rem; align-items: flex-start; }
    #modal-product-content .modal-product-img { width: 180px; height: 180px; object-fit: contain; border-radius: 12px; background: #f5f5f5; }
    #modal-product-content .modal-product-info { flex: 1; }
    #modal-product-content .modal-product-price { font-size: 1.3em; font-weight: bold; margin-top: 0.5em; }
    #modal-product-content .modal-reviews-section { margin-top: 2em; }
    #modal-product-content .review { border-bottom: 1px solid #eee; padding: 0.5em 0; }
    #modal-product-content .review-header { display: flex; gap: 1em; font-size: 0.95em; color: #555; align-items: center; }
    #modal-product-content .review-rating { color: #fbc02d; font-size: 1.1em; }
    #modal-product-content .review-user { font-weight: bold; }
    #modal-product-content .review-date { font-size: 0.9em; color: #888; }
    #modal-product-content .review-text { margin-top: 0.2em; }
    #modal-product-content .modal-loading, #modal-product-content .modal-error { text-align: center; margin: 2em 0; color: #888; }
    #modal-product-content #modal-review-form { margin-top: 1.5em; display: flex; flex-direction: column; gap: 0.7em; }
    #modal-product-content #modal-review-form textarea { width: 100%; resize: vertical; }
    #modal-product-content #modal-review-form button { align-self: flex-start; background: #1976d2; color: #fff; border: none; border-radius: 4px; padding: 0.5em 1.2em; font-size: 1em; cursor: pointer; margin-top: 0.5em; }
    #modal-product-content #modal-review-form button:hover { background: #1565c0; }
  `;
  document.head.appendChild(style);
})(); 