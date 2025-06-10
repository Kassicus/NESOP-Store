// Handles loading items, displaying storefront, and adding to cart
// Placeholder for storefront logic 

function showStore(username) {
  document.getElementById('app').innerHTML = `
    <div class="header">
      <span>Welcome, ${username}</span>
      <button id="logout-btn" style="float:right;">Logout</button>
    </div>
    <h2>Store Items</h2>
    <div class="store-items">
      <div class="item-placeholder"></div>
      <div class="item-placeholder"></div>
      <div class="item-placeholder"></div>
      <div class="item-placeholder"></div>
    </div>
  `;
  document.getElementById('logout-btn').onclick = function() {
    localStorage.removeItem('nesop_user');
    window.location.reload();
  };
} 