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

// Utility to format a timestamp as MST
function formatMST(dateString) {
  // Parse as UTC, then convert to MST (UTC-7, no DST)
  const date = new Date(dateString + 'Z'); // ensure UTC
  // Get UTC time, then subtract 7 hours for MST
  const mst = new Date(date.getTime() - 7 * 60 * 60 * 1000);
  // Format as e.g. 'Apr 27, 2024, 3:45 PM MST'
  return mst.toLocaleString('en-US', {
    year: 'numeric', month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit', hour12: true
  }) + ' MST';
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
              <span style="font-size:1.25em; margin-left: 0; padding-left: 0;">Welcome <b style="text-transform:capitalize;">${capitalizeFirstLetter(extractUsername(username))}</b>!</span>
              <span style="font-size:0.98em; color:#fff; margin-top:0.2em;">Balance: € ${balance}</span>
            </div>
            <div style="display: flex; align-items: center; gap: 0.5rem;">
              <a href="cart.html" class="cart-link" title="View Cart">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" class="cart-icon" width="32" height="32"><defs><style>.cls-1{fill:#231f20}</style></defs><g id="cart"><path class="cls-1" d="M29.46 10.14A2.94 2.94 0 0 0 27.1 9H10.22L8.76 6.35A2.67 2.67 0 0 0 6.41 5H3a1 1 0 0 0 0 2h3.41a.68.68 0 0 1 .6.31l1.65 3 .86 9.32a3.84 3.84 0 0 0 4 3.38h10.37a3.92 3.92 0 0 0 3.85-2.78l2.17-7.82a2.58 2.58 0 0 0-.45-2.27zM28 11.86l-2.17 7.83A1.93 1.93 0 0 1 23.89 21H13.48a1.89 1.89 0 0 1-2-1.56L10.73 11H27.1a1 1 0 0 1 .77.35.59.59 0 0 1 .13.51z"/><circle class="cls-1" cx="14" cy="26" r="2"/><circle class="cls-1" cx="24" cy="26" r="2"/></g></svg>
                <span id="cart-count-badge" class="cart-count-badge">0</span>
              </a>
              <button 
                type="button" 
                data-theme-toggle 
                aria-label="Change theme"
                class="theme-toggle-btn"
              >
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path></svg>
              </button>
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
    
    // Set up theme toggle
    setTimeout(setupThemeToggle, 100);
    
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
  productModal.className = 'modal-overlay';
  productModal.style.display = 'none';
  productModal.innerHTML = `
    <div class="modal">
      <button class="modal-close" id="modal-close-btn">&times;</button>
      <div id="modal-product-content"></div>
    </div>
  `;
  document.body.appendChild(productModal);
  productModal.querySelector('#modal-close-btn').onclick = closeProductModal;
  document.addEventListener('keydown', function(e) {
    if (productModal.style.display === 'flex' && e.key === 'Escape') closeProductModal();
  });
  return productModal;
}

function openProductModal(itemName) {
  const modal = createProductModal();
  modal.style.display = 'flex';
  document.body.style.overflow = 'hidden';
  document.getElementById('modal-product-content').innerHTML = '<div class="modal-loading">Loading...</div>';
  Promise.all([
    fetch(`/api/product/${encodeURIComponent(itemName)}`).then(r => r.json()),
    fetch(`/api/product/${encodeURIComponent(itemName)}/reviews`).then(r => r.json())
  ]).then(([product, reviewsData]) => {
    if (product.error) {
      document.getElementById('modal-product-content').innerHTML = `<div class="modal-error">${product.error}</div>`;
      return;
    }
    const reviews = reviewsData.reviews || [];
    document.getElementById('modal-product-content').innerHTML = `
      <div class="modal-title">${product.item}</div>
      <div class="modal-product-main">
        <img src="${product.image || 'assets/images/placeholder.png'}" alt="${product.item}" class="modal-product-img" onerror="this.onerror=null;this.src='assets/images/placeholder.png';" />
        <div class="modal-product-info">
          <h2 class="product-name" style="margin-top:0;">${product.item}</h2>
          <p class="product-desc">${product.description}</p>
          <div class="modal-product-price">€ ${product.price}</div>
          <button id="modal-add-cart-btn" class="action-btn add${product.sold_out ? ' sold-out-btn' : ''}" ${product.sold_out ? 'disabled' : ''} style="margin-top:1em;">${product.sold_out ? 'Sold Out' : 'Add to Cart'}</button>
        </div>
      </div>
      <form id="modal-review-form">
      <h3 style="color:#1976d2;">Leave a review!</h3>
        <div class="form-group">
          <label for="modal-review-rating">Rating:</label>
          <select id="modal-review-rating" name="rating" required>
            <option value="">Select</option>
            <option value="5">5 - Excellent</option>
            <option value="4">4 - Good</option>
            <option value="3">3 - Average</option>
            <option value="2">2 - Poor</option>
            <option value="1">1 - Terrible</option>
          </select>
        </div>
        <div class="form-group">
          <label for="modal-review-text">Review:</label>
          <textarea id="modal-review-text" name="review_text" rows="3" required></textarea>
        </div>
        <div class="form-group">
          <label for="modal-review-username">Your name (optional):</label>
          <input id="modal-review-username" type="text" name="username" />
        </div>
        <div class="modal-actions">
          <button type="submit" class="action-btn add">Submit Review</button>
          <button type="button" class="action-btn cancel" id="modal-review-cancel">Cancel</button>
        </div>
        <div id="modal-review-error" style="color:#e57373;margin-top:0.5em;"></div>
      </form>
      <div class="modal-reviews-section" style="margin-top:2.5em;">
        <h3 style="color:#1976d2;">Reviews</h3>
        <div id="modal-reviews-list">
          ${reviews.length === 0 ? '<p style="color:#888;">No reviews yet.</p>' : reviews.map(r => `
            <div class="review" data-review-id="${r.review_id}">
              <div class="review-header">
                <span class="review-user">${r.username ? r.username : 'Anonymous'}</span>
                <span class="review-rating">${'★'.repeat(r.rating)}${'☆'.repeat(5 - r.rating)}</span>
                <span class="review-date">${formatMST(r.timestamp)}</span>
                ${isAdminUser() ? `<button class="review-delete-btn action-btn delete" title="Delete Review" style="margin-left:0.5em;">Remove</button>` : ''}
              </div>
              <div class="review-text">${r.review_text}</div>
            </div>
          `).join('')}
        </div>
      </div>
    `;
    // Add to Cart button logic
    const addCartBtn = document.getElementById('modal-add-cart-btn');
    if (addCartBtn && !product.sold_out) {
      addCartBtn.onclick = function() {
        const cart = getCart();
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
          fetch(`/api/product/${encodeURIComponent(itemName)}/reviews`).then(r => r.json()).then(reviewsData2 => {
            const reviews2 = reviewsData2.reviews || [];
            document.getElementById('modal-reviews-list').innerHTML = reviews2.length === 0 ? '<p style="color:#888;">No reviews yet.</p>' : reviews2.map(r => `
              <div class="review" data-review-id="${r.review_id}">
                <div class="review-header">
                  <span class="review-user">${r.username ? r.username : 'Anonymous'}</span>
                  <span class="review-rating">${'★'.repeat(r.rating)}${'☆'.repeat(5 - r.rating)}</span>
                  <span class="review-date">${formatMST(r.timestamp)}</span>
                  ${isAdminUser() ? `<button class="review-delete-btn action-btn delete" title="Delete Review" style="margin-left:0.5em;">Remove</button>` : ''}
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
    // Cancel button closes modal
    document.getElementById('modal-review-cancel').onclick = closeProductModal;
    // Admin review delete logic
    if (isAdminUser()) {
      document.querySelectorAll('.review-delete-btn').forEach(btn => {
        btn.onclick = function(e) {
          e.preventDefault();
          const reviewDiv = this.closest('.review');
          const reviewId = reviewDiv.getAttribute('data-review-id');
          if (!confirm('Are you sure you want to delete this review?')) return;
          const username = localStorage.getItem('nesop_user');
          fetch(`/api/product/${encodeURIComponent(itemName)}/reviews/${reviewId}`, {
            method: 'DELETE',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username })
          }).then(r => r.json()).then(resp => {
            if (!resp.success) {
              alert(resp.error || 'Failed to delete review.');
            } else {
              reviewDiv.remove();
            }
          }).catch(() => {
            alert('Failed to delete review.');
          });
        };
      });
    }
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
    #product-modal.modal-overlay {
      position: fixed; top: 0; left: 0; right: 0; bottom: 0;
      background: var(--color-modal-overlay); z-index: 1000;
      display: flex; align-items: center; justify-content: center;
      transition: opacity 0.2s;
    }
    #product-modal .modal {
      background: var(--color-card-bg); border-radius: 10px;
      box-shadow: 0 4px 24px var(--color-shadow-hover);
      padding: 2rem 2.5rem; min-width: 320px; max-width: 95vw;
      z-index: 1001; position: relative; animation: modalIn 0.2s;
      transition: background-color 0.3s ease;
    }
    @keyframes modalIn {
      from { transform: scale(0.95); opacity: 0; }
      to { transform: scale(1); opacity: 1; }
    }
    #product-modal .modal-title {
      font-size: 1.35rem; font-weight: 600; letter-spacing: 0.5px;
      color: #1976d2; margin-bottom: 1.2rem;
    }
    #product-modal .modal-close {
      position: absolute; top: 1.2rem; right: 1.2rem;
      background: none; border: none; font-size: 2rem; color: #1976d2;
      cursor: pointer; transition: color 0.2s;
    }
    #product-modal .modal-close:hover { color: #f27a12; }
    #product-modal .modal-product-main { display: flex; gap: 2rem; align-items: flex-start; }
    #product-modal .modal-product-img { width: 140px; height: 140px; object-fit: contain; border-radius: 8px; background: var(--color-product-img-bg); box-shadow: 0 1px 4px var(--color-shadow-light); transition: background-color 0.3s ease; }
    #product-modal .modal-product-info { flex: 1; color: var(--color-fg); }
    #product-modal .modal-product-price { font-size: 1.2em; font-weight: bold; margin-top: 0.5em; color: #1976d2; }
    #product-modal .modal-reviews-section { margin-top: 2em; }
    #product-modal .review { border-bottom: 1px solid var(--color-border-light); padding: 0.5em 0; transition: border-color 0.3s ease; }
    #product-modal .review-header { display: flex; gap: 1em; font-size: 0.95em; color: var(--color-text-secondary); align-items: center; }
    #product-modal .review-rating { color: #fbc02d; font-size: 1.1em; }
    #product-modal .review-user { font-weight: bold; color: #1976d2; }
    #product-modal .review-date { font-size: 0.9em; color: var(--color-text-muted); }
    #product-modal .review-text { margin-top: 0.2em; color: var(--color-fg); }
    #product-modal .modal-loading, #product-modal .modal-error { text-align: center; margin: 2em 0; color: var(--color-text-muted); }
    #product-modal #modal-review-form { margin-top: 1.5em; }
    #product-modal .form-group { margin-bottom: 1rem; }
    #product-modal .form-group label { display: block; font-weight: bold; margin-bottom: 0.3rem; color: #1976d2; }
    #product-modal .form-group input, #product-modal .form-group textarea, #product-modal .form-group select {
      display: block; width: 100%; padding: 0.5rem; border-radius: 4px; border: 1px solid var(--color-border); font-size: 1rem;
      margin-bottom: 0.2rem; background: var(--color-input-bg); color: var(--color-fg);
      transition: background-color 0.3s ease, color 0.3s ease, border-color 0.3s ease;
    }
    #product-modal .modal-actions { display: flex; justify-content: flex-end; gap: 1rem; margin-top: 1rem; }
    #product-modal .action-btn {
      background: #1976d2; color: #fff; border: none; border-radius: 4px;
      padding: 0.4rem 0.8rem; font-weight: bold; font-size: 0.9rem; cursor: pointer; transition: background 0.2s;
    }
    #product-modal .action-btn.cancel { background: #9e9e9e; }
    #product-modal .action-btn.save, #product-modal .action-btn.add { background: #1976d2; }
    #product-modal .action-btn.cancel:hover { background: #757575; }
    #product-modal .action-btn.save:hover, #product-modal .action-btn.add:hover { background: #125ea7; }
    @media (max-width: 700px) {
      #product-modal .modal { padding: 1rem 0.5rem; }
      #product-modal .modal-product-main { flex-direction: column; gap: 1rem; align-items: stretch; }
      #product-modal .modal-product-img { width: 100%; height: 120px; }
    }
  `;
  document.head.appendChild(style);
})();

// Helper to check if user is admin
function isAdminUser() {
  return localStorage.getItem('nesop_user_admin') === 'true';
} 