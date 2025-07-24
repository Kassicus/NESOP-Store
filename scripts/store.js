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
    fetch('/api/items').then(res => {
      if (!res.ok) {
        throw new Error(`HTTP error! status: ${res.status}`);
      }
      return res.json();
    }),
    fetch('/api/users').then(res => {
      if (!res.ok) {
        throw new Error(`HTTP error! status: ${res.status}`);
      }
      return res.json();
    })
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
              <span style="font-size:0.98em; color:#fff; margin-top:0.2em;">Balance: ₦ ${balance}</span>
            </div>
            <nav class="header-nav" style="display: flex; align-items: center; gap: 0.5rem;">
              <!-- User Account -->
              <button onclick="window.location.href='account.html'" class="nav-btn" title="My Account">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                  <circle cx="12" cy="7" r="4"></circle>
                </svg>
              </button>
              
              <!-- Cart -->
              <button onclick="window.location.href='cart.html'" class="nav-btn" title="Shopping Cart">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <circle cx="9" cy="21" r="1"></circle>
                  <circle cx="20" cy="21" r="1"></circle>
                  <path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"></path>
                </svg>
                <span id="cart-count-badge" class="cart-count-badge">0</span>
              </button>
              
              <!-- Store (current page, different styling) -->
              <button class="nav-btn nav-btn-active" title="Store">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path>
                  <polyline points="9,22 9,12 15,12 15,22"></polyline>
                </svg>
              </button>
              
              <!-- Theme Toggle -->
              <button type="button" data-theme-toggle aria-label="Change theme" class="nav-btn">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path>
                </svg>
              </button>
              
              <!-- Admin (visible to admins only) -->
              <button onclick="window.location.href='admin-dashboard.html'" class="nav-btn admin-only ${isAdmin ? 'show' : ''}" title="Admin Panel">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4z"></path>
                </svg>
              </button>
              
              <!-- Logout -->
              <button id="logout-btn" class="nav-btn logout-btn" title="Logout">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path>
                  <polyline points="16,17 21,12 16,7"></polyline>
                  <line x1="21" y1="12" x2="9" y2="12"></line>
                </svg>
              </button>
            </nav>
          </div>
        </div>
      </header>
      
      <!-- Modern Shop Interface -->
      <main class="store-main">
        <div class="container">
          <!-- Search and Filter Section -->
          <div class="shop-controls">
            <div class="search-section">
              <div class="search-container">
                <svg class="search-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <circle cx="11" cy="11" r="8"></circle>
                  <path d="21 21l-4.35-4.35"></path>
                </svg>
                <input 
                  type="text" 
                  id="product-search" 
                  placeholder="Search products..." 
                  class="search-input"
                />
              </div>
            </div>
            <div class="filter-section">
              <select id="sort-products" class="modern-select">
                <option value="name-asc">Name (A-Z)</option>
                <option value="name-desc">Name (Z-A)</option>
                <option value="price-asc">Price (Low-High)</option>
                <option value="price-desc">Price (High-Low)</option>
                <option value="available">Available First</option>
              </select>
              <select id="filter-availability" class="modern-select">
                <option value="all">All Products</option>
                <option value="available">In Stock</option>
                <option value="sold-out">Sold Out</option>
              </select>
            </div>
          </div>

          <!-- Products Grid -->
          <div class="products-section">
            <div class="section-header">
              <h2>Our Products</h2>
              <div class="results-info" id="results-count">Loading products...</div>
            </div>
            
            <!-- Loading State -->
            <div class="loading-state" id="loading-products">
              <div class="loading-spinner"></div>
              <p>Loading amazing products...</p>
            </div>
            
            <!-- Products Grid -->
            <div class="modern-product-grid" id="store-items">
              <!-- Products will be rendered here -->
            </div>

            <!-- Empty State -->
            <div class="empty-state" id="no-products" style="display: none;">
              <div class="empty-icon">🔍</div>
              <h3>No products found</h3>
              <p>Try adjusting your search or filter criteria.</p>
            </div>
          </div>
        </div>
      </main>
    `;
    
    // Initialize shop functionality
    initializeShop();
    
    // Set up logout
    document.getElementById('logout-btn').onclick = function() {
      window.nesopLogout();
    };
    
    // Set up theme toggle
    setTimeout(setupThemeToggle, 100);
    
         // Initialize products
     setTimeout(() => {
       renderModernItems(items);
       setupSearchAndFilters();
       updateCartCount();
     }, 100);
  }).catch(err => {
    console.error('Error loading store data:', err);
    document.getElementById('app').innerHTML = `
      <div style="padding: 2rem; text-align: center;">
        <h2 style="color: red;">Failed to load store data</h2>
        <p style="color: #666;">There was an error connecting to the server.</p>
        <details style="margin-top: 1rem; text-align: left; background: #f5f5f5; padding: 1rem; border-radius: 4px;">
          <summary style="cursor: pointer; font-weight: bold;">Error Details</summary>
          <pre style="margin-top: 0.5rem; white-space: pre-wrap;">${err.message}</pre>
        </details>
        <button onclick="location.reload()" style="margin-top: 1rem; padding: 0.5rem 1rem; background: #1976d2; color: white; border: none; border-radius: 4px; cursor: pointer;">
          Retry
        </button>
      </div>
    `;
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
  
  // Close button click handler
  productModal.querySelector('#modal-close-btn').onclick = closeProductModal;
  
  // Click outside modal to close
  productModal.addEventListener('click', function(e) {
    if (e.target === productModal) {
      closeProductModal();
    }
  });
  
  // Prevent modal content clicks from bubbling up to the overlay
  productModal.querySelector('.modal').addEventListener('click', function(e) {
    e.stopPropagation();
  });
  
  // Escape key to close
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
      <div class="modal-header">
        <div class="modal-title">${product.item}</div>
        <button class="modal-close" onclick="closeProductModal()">&times;</button>
      </div>
      <div class="modal-content">
        <div class="modal-product-main">
          <div class="modal-product-image-container">
            <img src="${product.image || 'assets/images/placeholder.png'}" alt="${product.item}" class="modal-product-img" onerror="this.onerror=null;this.src='assets/images/placeholder.png';" />
          </div>
          <div class="modal-product-info">
            <h2 class="product-name">${product.item}</h2>
            <p class="product-desc">${product.description}</p>
            <div class="modal-product-price">₦${parseFloat(product.price).toLocaleString()}</div>
            <button id="modal-add-cart-btn" class="modern-add-cart-btn${product.sold_out ? ' sold-out-btn' : ''}" ${product.sold_out ? 'disabled' : ''}>${product.sold_out ? '❌ Sold Out' : '🛒 Add to Cart'}</button>
          </div>
        </div>
        <form id="modal-review-form">
          <h3>Leave a review!</h3>
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
              <div class="modal-reviews-section">
          <h3>Reviews</h3>
                    <div id="modal-reviews-list">
              ${reviews.length === 0 ? '<p style="color:#888;">No reviews yet.</p>' : reviews.map(r => `
                <div class="review" data-review-id="${r.review_id}">
                  <div class="review-header">
                    <span class="review-user">${r.username ? r.username : 'Anonymous'}</span>
                    <span class="review-rating">${'★'.repeat(r.rating)}${'☆'.repeat(5 - r.rating)}</span>
                    <span class="review-date">${formatMST(r.timestamp)}</span>
                    ${isAdminUser() ? `<button class="review-delete-btn action-btn delete" title="Delete Review">Remove</button>` : ''}
                  </div>
                  <div class="review-text">${r.review_text}</div>
                </div>
              `).join('')}
          </div>
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
                  ${isAdminUser() ? `<button class="review-delete-btn action-btn delete" title="Delete Review">Remove</button>` : ''}
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

// Modern shop initialization
let currentItems = [];
let filteredItems = [];
let searchQuery = '';
let sortBy = 'name-asc';
let filterBy = 'all';

function initializeShop() {
  // Any initial shop setup can go here
  console.log('🏪 Modern shop initialized');
}



function renderModernItems(items) {
  currentItems = items.filter(item => !item.unlisted);
  filteredItems = [...currentItems];
  
  // Hide loading state
  const loading = document.getElementById('loading-products');
  if (loading) loading.style.display = 'none';
  
  applyFiltersAndSort();
}

function applyFiltersAndSort() {
  let filtered = [...currentItems];
  
  // Apply search filter
  if (searchQuery.trim()) {
    filtered = filtered.filter(item => 
      item.item.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.description.toLowerCase().includes(searchQuery.toLowerCase())
    );
  }
  
  // Apply availability filter
  if (filterBy === 'available') {
    filtered = filtered.filter(item => !item.sold_out);
  } else if (filterBy === 'sold-out') {
    filtered = filtered.filter(item => item.sold_out);
  }
  
  // Apply sorting
  filtered.sort((a, b) => {
    switch (sortBy) {
      case 'name-asc':
        return a.item.localeCompare(b.item);
      case 'name-desc':
        return b.item.localeCompare(a.item);
      case 'price-asc':
        return parseFloat(a.price) - parseFloat(b.price);
      case 'price-desc':
        return parseFloat(b.price) - parseFloat(a.price);
      case 'available':
        return (a.sold_out ? 1 : 0) - (b.sold_out ? 1 : 0);
      default:
        return 0;
    }
  });
  
  filteredItems = filtered;
  renderProductCards();
  updateResultsCount();
}

function renderProductCards() {
  const container = document.getElementById('store-items');
  const noProducts = document.getElementById('no-products');
  
  if (!container) return;
  
  if (filteredItems.length === 0) {
    container.style.display = 'none';
    noProducts.style.display = 'flex';
    return;
  }
  
  container.style.display = 'grid';
  noProducts.style.display = 'none';
  
  container.innerHTML = filteredItems.map((item, idx) => {
    const inCart = getCart().some(cartItem => cartItem.item === item.item);
    const quantity = item.quantity || 0;
    let stockBadge;
    
    if (item.sold_out) {
      stockBadge = '<span class="stock-badge sold-out">Sold Out</span>';
    } else if (quantity === 0) {
      stockBadge = '<span class="stock-badge sold-out">Out of Stock</span>';
    } else if (quantity <= 5) {
      stockBadge = `<span class="stock-badge low-stock">Only ${quantity} left</span>`;
    } else {
      stockBadge = '<span class="stock-badge in-stock">Available</span>';
    }
    
    return `
      <div class="modern-product-card ${item.sold_out ? 'sold-out' : ''}" data-item="${item.item}">
        <div class="product-image-container">
          <img 
            src="${item.image || 'assets/images/placeholder.png'}" 
            alt="${item.item}" 
            class="modern-product-img" 
            onerror="this.onerror=null;this.src='assets/images/placeholder.png';" 
          />
          ${stockBadge}
          <div class="product-overlay">
            <button class="quick-view-btn" data-item="${item.item}">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
                <circle cx="12" cy="12" r="3"></circle>
              </svg>
              Quick View
            </button>
          </div>
        </div>
        
        <div class="modern-product-info">
          <h3 class="modern-product-name">${item.item}</h3>
          <p class="modern-product-desc">${item.description}</p>
          
          <div class="product-price-section">
            <span class="modern-product-price">₦${parseFloat(item.price).toLocaleString()}</span>
          </div>
          
          <div class="product-actions">
            <button 
              class="modern-add-cart-btn ${item.sold_out || quantity === 0 ? 'sold-out-btn' : ''} ${inCart ? 'in-cart' : ''}" 
              data-idx="${idx}" 
              ${item.sold_out || quantity === 0 ? 'disabled' : ''}
            >
              ${item.sold_out || quantity === 0 ? 
                '<span>❌ Out of Stock</span>' : 
                inCart ? 
                  '<span>✅ In Cart</span>' : 
                  '<span>🛒 Add to Cart</span>'
              }
            </button>
          </div>
        </div>
      </div>
    `;
  }).join('');

  // Add event listeners
  setupProductCardListeners();
}

function setupProductCardListeners() {
  const container = document.getElementById('store-items');
  if (!container) return;

  // Add to cart buttons
  container.querySelectorAll('.modern-add-cart-btn').forEach(btn => {
    if (btn.disabled || btn.classList.contains('in-cart')) return;
    
    btn.addEventListener('click', function(e) {
      e.stopPropagation();
      const idx = parseInt(this.getAttribute('data-idx'));
      const item = filteredItems[idx];
      
      // Check if item has inventory available
      const quantity = item.quantity || 0;
      if (item.sold_out || quantity === 0) {
        return; // Don't add out of stock items
      }
      
      const cart = getCart();
      if (!cart.find(i => i.item === item.item)) {
        cart.push(item);
        setCart(cart);
        updateCartCount();
        
        // Update button state
        this.innerHTML = '<span>✅ Added!</span>';
        this.classList.add('in-cart');
        this.disabled = true;
        
        // Show success feedback
        showCartFeedback(item.item);
        
        setTimeout(() => {
          // Re-render to update all buttons
          renderProductCards();
        }, 1500);
      }
    });
  });

  // Quick view buttons
  container.querySelectorAll('.quick-view-btn').forEach(btn => {
    btn.addEventListener('click', function(e) {
      e.stopPropagation();
      const itemName = this.getAttribute('data-item');
      openProductModal(itemName);
    });
  });

  // Product card clicks
  container.querySelectorAll('.modern-product-card').forEach(card => {
    card.addEventListener('click', function() {
      const itemName = this.getAttribute('data-item');
      openProductModal(itemName);
    });
  });
}

function updateResultsCount() {
  const resultsElement = document.getElementById('results-count');
  if (!resultsElement) return;
  
  const total = currentItems.length;
  const showing = filteredItems.length;
  
  if (showing === total) {
    resultsElement.textContent = `Showing all ${total} products`;
  } else {
    resultsElement.textContent = `Showing ${showing} of ${total} products`;
  }
}

function setupSearchAndFilters() {
  const searchInput = document.getElementById('product-search');
  const sortSelect = document.getElementById('sort-products');
  const filterSelect = document.getElementById('filter-availability');
  
  if (searchInput) {
    searchInput.addEventListener('input', debounce((e) => {
      searchQuery = e.target.value;
      applyFiltersAndSort();
    }, 300));
  }
  
  if (sortSelect) {
    sortSelect.addEventListener('change', (e) => {
      sortBy = e.target.value;
      applyFiltersAndSort();
    });
  }
  
  if (filterSelect) {
    filterSelect.addEventListener('change', (e) => {
      filterBy = e.target.value;
      applyFiltersAndSort();
    });
  }
}

function showCartFeedback(itemName) {
  // Create temporary feedback element
  const feedback = document.createElement('div');
  feedback.className = 'cart-feedback';
  feedback.innerHTML = `
    <div class="cart-feedback-content">
      <div class="cart-feedback-icon">🛒</div>
      <div class="cart-feedback-text">
        <strong>${itemName}</strong><br>
        Added to cart!
      </div>
    </div>
  `;
  
  document.body.appendChild(feedback);
  
  // Remove after animation
  setTimeout(() => {
    feedback.remove();
  }, 3000);
}

function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

// Legacy function for backwards compatibility
function renderItems(items) {
  renderModernItems(items);
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

// --- Modern Modal Styles ---
(function() {
  const style = document.createElement('style');
  style.innerHTML = `
    /* Modal Overlay - Enhanced */
    #product-modal.modal-overlay {
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background: var(--color-modal-overlay);
      backdrop-filter: blur(4px);
      z-index: 1000;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: all 0.3s ease;
      padding: 1rem;
    }
    
    /* Modern Modal Container */
    #product-modal .modal {
      background: var(--color-card-bg);
      border-radius: 24px;
      box-shadow: 0 20px 60px rgba(25, 118, 210, 0.15), 0 8px 32px rgba(0, 0, 0, 0.1);
      padding: 0;
      min-width: 360px;
      max-width: 90vw;
      max-height: 90vh;
      width: 100%;
      max-width: 800px;
      z-index: 1001;
      position: relative;
      animation: modalIn 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
      transition: background-color 0.3s ease;
      overflow: hidden;
      border: 1px solid var(--color-border-light);
    }
    
    @keyframes modalIn {
      from { 
        transform: scale(0.9) translateY(20px); 
        opacity: 0; 
      }
      to { 
        transform: scale(1) translateY(0); 
        opacity: 1; 
      }
    }
    
         /* Modal Header */
     .modal-header {
       background: linear-gradient(135deg, #1976d2 0%, #1565c0 100%);
       color: white;
       padding: 1.25rem 2rem 1rem;
       position: relative;
       border-radius: 24px 24px 0 0;
     }
     
     #product-modal .modal-title {
       font-size: 1.4rem;
       font-weight: 700;
       letter-spacing: 0.5px;
       color: white;
       margin: 0;
       line-height: 1.3;
     }
    
         /* Modern Close Button */
     #product-modal .modal-close {
       position: absolute;
       top: 1rem;
       right: 1.5rem;
       background: rgba(255, 255, 255, 0.15);
       backdrop-filter: blur(10px);
       border: 1px solid rgba(255, 255, 255, 0.2);
       border-radius: 10px;
       width: 36px;
       height: 36px;
       font-size: 1.3rem;
       color: white;
       cursor: pointer;
       transition: all 0.3s ease;
       display: flex;
       align-items: center;
       justify-content: center;
     }
    
    #product-modal .modal-close:hover {
      background: rgba(244, 67, 54, 0.2);
      border-color: rgba(244, 67, 54, 0.3);
      transform: scale(1.05);
    }
    
         /* Modal Content Area */
     .modal-content {
       padding: 1.5rem 2rem;
       overflow-y: auto;
       max-height: calc(90vh - 100px);
     }
     
     /* Product Main Section - Enhanced Layout */
     #product-modal .modal-product-main {
       display: grid;
       grid-template-columns: 1fr 1.5fr;
       gap: 2rem;
       align-items: start;
       margin-bottom: 2rem;
     }
    
         /* Enhanced Product Image */
     .modal-product-image-container {
       position: relative;
       background: var(--color-product-img-bg);
       border-radius: 16px;
       padding: 1.25rem;
       box-shadow: 0 6px 24px var(--color-shadow);
       transition: all 0.3s ease;
     }
     
     #product-modal .modal-product-img {
       width: 100%;
       height: 200px;
       object-fit: contain;
       border-radius: 8px;
       transition: all 0.3s ease;
     }
    
    .modal-product-image-container:hover {
      transform: scale(1.02);
      box-shadow: 0 12px 40px var(--color-shadow-hover);
    }
    
    /* Product Info Section */
    #product-modal .modal-product-info {
      flex: 1;
      color: var(--color-fg);
    }
    
         #product-modal .product-name {
       font-size: 1.3rem;
       font-weight: 700;
       color: #1976d2;
       margin: 0 0 0.75rem 0;
       line-height: 1.3;
     }
     
     #product-modal .product-desc {
       font-size: 1rem;
       color: var(--color-text-secondary);
       line-height: 1.5;
       margin-bottom: 1.25rem;
     }
     
     /* Modern Price Display */
     #product-modal .modal-product-price {
       font-size: 1.6rem;
       font-weight: 800;
       color: #1976d2;
       margin-bottom: 1.25rem;
       display: flex;
       align-items: center;
       gap: 0.5rem;
     }
    
         /* Modern Add to Cart Button */
     #product-modal #modal-add-cart-btn {
       background: linear-gradient(135deg, #1976d2 0%, #1565c0 100%);
       color: white;
       border: none;
       border-radius: 12px;
       padding: 0.75rem 1.5rem;
       font-weight: 700;
       font-size: 1rem;
       cursor: pointer;
       transition: all 0.3s ease;
       width: 100%;
       display: flex;
       align-items: center;
       justify-content: center;
       gap: 0.5rem;
       box-shadow: 0 4px 16px rgba(25, 118, 210, 0.3);
     }
    
    #product-modal #modal-add-cart-btn:hover:not(:disabled) {
      transform: translateY(-2px);
      box-shadow: 0 8px 24px rgba(25, 118, 210, 0.4);
      background: linear-gradient(135deg, #1565c0 0%, #0d47a1 100%);
    }
    
    #product-modal #modal-add-cart-btn.sold-out-btn {
      background: linear-gradient(135deg, #f44336 0%, #d32f2f 100%);
      cursor: not-allowed;
      box-shadow: 0 4px 16px rgba(244, 67, 54, 0.3);
    }
    
         /* Reviews Section - Modern Design */
     #product-modal .modal-reviews-section {
       margin-top: 2rem;
       padding-top: 1.5rem;
       border-top: 2px solid var(--color-border-light);
     }
     
     #product-modal .modal-reviews-section h3 {
       font-size: 1.3rem;
       font-weight: 700;
       color: #1976d2;
       margin-bottom: 1.25rem;
       display: flex;
       align-items: center;
       gap: 0.5rem;
     }
    
    #product-modal .modal-reviews-section h3::before {
      content: "⭐";
      font-size: 1.25rem;
    }
    
         /* Enhanced Review Cards */
     #product-modal .review {
       background: var(--color-card-bg);
       border: 1px solid var(--color-border-light);
       border-radius: 12px;
       padding: 1rem;
       margin-bottom: 0.75rem;
       transition: all 0.3s ease;
       box-shadow: 0 2px 8px var(--color-shadow-light);
     }
    
    #product-modal .review:hover {
      transform: translateY(-2px);
      box-shadow: 0 8px 24px var(--color-shadow);
      border-color: #1976d2;
    }
    
         #product-modal .review-header {
       display: flex;
       align-items: center;
       gap: 0.75rem;
       margin-bottom: 0.75rem;
       flex-wrap: wrap;
     }
    
    #product-modal .review-user {
      font-weight: 700;
      color: #1976d2;
      font-size: 1rem;
    }
    
    #product-modal .review-rating {
      color: #ffc107;
      font-size: 1.2rem;
      letter-spacing: 2px;
    }
    
    #product-modal .review-date {
      font-size: 0.9rem;
      color: var(--color-text-muted);
      margin-left: auto;
    }
    
    #product-modal .review-text {
      color: var(--color-fg);
      line-height: 1.6;
      font-size: 1rem;
    }
    
         /* Modern Review Form */
     #product-modal #modal-review-form {
       background: var(--color-card-bg);
       border: 2px solid var(--color-border-light);
       border-radius: 16px;
       padding: 1.5rem;
       margin-top: 1.5rem;
       box-shadow: 0 4px 16px var(--color-shadow-light);
     }
     
     #product-modal #modal-review-form h3 {
       color: #1976d2;
       font-size: 1.2rem;
       font-weight: 700;
       margin: 0 0 1.25rem 0;
       display: flex;
       align-items: center;
       gap: 0.5rem;
     }
    
    #product-modal #modal-review-form h3::before {
      content: "✍️";
      font-size: 1.1rem;
    }
    
         #product-modal .form-group {
       margin-bottom: 1.25rem;
     }
    
    #product-modal .form-group label {
      display: block;
      font-weight: 600;
      margin-bottom: 0.5rem;
      color: #1976d2;
      font-size: 1rem;
    }
    
         #product-modal .form-group input,
     #product-modal .form-group textarea,
     #product-modal .form-group select {
       display: block;
       width: 100%;
       padding: 0.75rem 1rem;
       border-radius: 8px;
       border: 2px solid var(--color-border);
       font-size: 1rem;
       background: var(--color-input-bg);
       color: var(--color-fg);
       transition: all 0.3s ease;
       box-sizing: border-box;
     }
    
    #product-modal .form-group input:focus,
    #product-modal .form-group textarea:focus,
    #product-modal .form-group select:focus {
      outline: none;
      border-color: #1976d2;
      box-shadow: 0 0 0 3px rgba(25, 118, 210, 0.1);
      transform: translateY(-1px);
    }
    
         #product-modal .form-group textarea {
       resize: vertical;
       min-height: 80px;
     }
    
         /* Modern Form Actions */
     #product-modal .modal-actions {
       display: flex;
       gap: 1rem;
       margin-top: 1.5rem;
       justify-content: flex-end;
     }
    
    #product-modal .action-btn {
      border: none;
      border-radius: 12px;
      padding: 0.875rem 1.5rem;
      font-weight: 600;
      font-size: 1rem;
      cursor: pointer;
      transition: all 0.3s ease;
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }
    
    #product-modal .action-btn.add {
      background: linear-gradient(135deg, #1976d2 0%, #1565c0 100%);
      color: white;
      box-shadow: 0 4px 16px rgba(25, 118, 210, 0.3);
    }
    
    #product-modal .action-btn.add:hover {
      transform: translateY(-2px);
      box-shadow: 0 8px 24px rgba(25, 118, 210, 0.4);
    }
    
    #product-modal .action-btn.cancel {
      background: var(--color-border);
      color: var(--color-text-secondary);
      border: 2px solid var(--color-border);
    }
    
    #product-modal .action-btn.cancel:hover {
      background: var(--color-text-muted);
      color: white;
      transform: translateY(-1px);
    }
    
    #product-modal .action-btn.delete {
      background: linear-gradient(135deg, #f44336 0%, #d32f2f 100%);
      color: white;
      box-shadow: 0 4px 16px rgba(244, 67, 54, 0.3);
    }
    
    #product-modal .action-btn.delete:hover {
      transform: translateY(-2px);
      box-shadow: 0 8px 24px rgba(244, 67, 54, 0.4);
    }
    
    /* Loading and Error States */
    #product-modal .modal-loading,
    #product-modal .modal-error {
      text-align: center;
      padding: 3rem 2rem;
      color: var(--color-text-muted);
      font-size: 1.1rem;
    }
    
    #product-modal .modal-loading::before {
      content: "⏳";
      font-size: 2rem;
      display: block;
      margin-bottom: 1rem;
    }
    
    #product-modal .modal-error {
      color: #f44336;
    }
    
    #product-modal .modal-error::before {
      content: "❌";
      font-size: 2rem;
      display: block;
      margin-bottom: 1rem;
    }
    
    /* Mobile Responsive Design */
    @media (max-width: 768px) {
      #product-modal .modal {
        margin: 0.5rem;
        border-radius: 20px;
        max-width: calc(100vw - 1rem);
      }
      
      .modal-header {
        padding: 1.5rem 1.5rem 1rem;
      }
      
      #product-modal .modal-title {
        font-size: 1.4rem;
        margin-right: 3rem;
      }
      
      #product-modal .modal-close {
        top: 1rem;
        right: 1rem;
        width: 36px;
        height: 36px;
        font-size: 1.2rem;
      }
      
      .modal-content {
        padding: 1.5rem;
      }
      
      #product-modal .modal-product-main {
        grid-template-columns: 1fr;
        gap: 2rem;
      }
      
      #product-modal .modal-product-img {
        height: 200px;
      }
      
      #product-modal .modal-product-price {
        font-size: 1.5rem;
      }
      
      #product-modal .modal-actions {
        flex-direction: column-reverse;
      }
      
      #product-modal .action-btn {
        width: 100%;
        justify-content: center;
      }
    }
    
    @media (max-width: 480px) {
      .modal-header {
        padding: 1rem;
      }
      
      #product-modal .modal-title {
        font-size: 1.2rem;
      }
      
      .modal-content {
        padding: 1rem;
      }
      
      .modal-product-image-container {
        padding: 1rem;
      }
      
      #product-modal .modal-product-img {
        height: 160px;
      }
      
      #product-modal #modal-review-form {
        padding: 1.5rem;
      }
    }
  `;
  document.head.appendChild(style);
})();

// Helper to check if user is admin
function isAdminUser() {
  return localStorage.getItem('nesop_user_admin') === 'true';
} 