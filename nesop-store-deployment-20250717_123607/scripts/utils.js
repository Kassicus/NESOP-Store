// Shared utility functions (e.g., formatting, logging)

// Extract username from email address (e.g., "user@domain.com" -> "user")
function extractUsername(usernameOrEmail) {
  if (!usernameOrEmail) return '';
  
  // If it contains @, extract the part before @
  if (usernameOrEmail.includes('@')) {
    return usernameOrEmail.split('@')[0];
  }
  
  // If it contains \, extract the part after \ (for domain\username format)
  if (usernameOrEmail.includes('\\')) {
    return usernameOrEmail.split('\\')[1];
  }
  
  // Otherwise, return as is
  return usernameOrEmail;
}

// Theme Toggle Functionality
function calculateSettingAsThemeString({ localStorageTheme, systemSettingDark }) {
  if (localStorageTheme !== null) {
    return localStorageTheme;
  }
  
  if (systemSettingDark.matches) {
    return "dark";
  }
  
  return "light";
}

function updateThemeOnHtmlEl({ theme }) {
  document.documentElement.setAttribute("data-theme", theme);
}

function updateThemeToggleText({ theme }) {
  const button = document.querySelector("[data-theme-toggle]");
  if (button) {
    const newCta = theme === "dark" ? "Switch to light theme" : "Switch to dark theme";
    button.setAttribute("aria-label", newCta);
    
    // Update button content (sun/moon icons)
    const sunIcon = `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="5"></circle><line x1="12" y1="1" x2="12" y2="3"></line><line x1="12" y1="21" x2="12" y2="23"></line><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line><line x1="1" y1="12" x2="3" y2="12"></line><line x1="21" y1="12" x2="23" y2="12"></line><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line></svg>`;
    const moonIcon = `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path></svg>`;
    
    button.innerHTML = theme === "dark" ? sunIcon : moonIcon;
  }
}

// Initialize theme on page load
function initializeTheme() {
  const localStorageTheme = localStorage.getItem("theme");
  const systemSettingDark = window.matchMedia("(prefers-color-scheme: dark)");
  
  let currentThemeSetting = calculateSettingAsThemeString({ 
    localStorageTheme, 
    systemSettingDark 
  });
  
  updateThemeOnHtmlEl({ theme: currentThemeSetting });
  updateThemeToggleText({ theme: currentThemeSetting });
  
  return currentThemeSetting;
}

// Set up theme toggle functionality
function setupThemeToggle() {
  let currentThemeSetting = initializeTheme();
  
  const button = document.querySelector("[data-theme-toggle]");
  if (button) {
    button.addEventListener("click", () => {
      const newTheme = currentThemeSetting === "dark" ? "light" : "dark";
      
      localStorage.setItem("theme", newTheme);
      updateThemeToggleText({ theme: newTheme });
      updateThemeOnHtmlEl({ theme: newTheme });
      
      currentThemeSetting = newTheme;
    });
  }
}

// Create theme toggle button HTML
function createThemeToggleButton() {
  return `
    <button 
      type="button" 
      data-theme-toggle 
      aria-label="Change theme"
      style="
        background: rgba(255,255,255,0.18);
        color: #fff;
        border: none;
        border-radius: 4px;
        padding: 0.6rem;
        font-weight: bold;
        cursor: pointer;
        transition: background 0.2s;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-right: 0.5rem;
      "
      onmouseover="this.style.background='#125ea7'"
      onmouseout="this.style.background='rgba(255,255,255,0.18)'"
    >
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path></svg>
    </button>
  `;
}

// Auto-initialize theme when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
  initializeTheme();
  
  // Set up theme toggle after a short delay to ensure button exists
  setTimeout(setupThemeToggle, 100);
}); 