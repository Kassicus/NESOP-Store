<?php
/**
 * Configuration Template File
 * 
 * Copy this file to config.php and update the values with your actual configuration
 */

// Database Configuration
define('DB_HOST', 'localhost');
define('DB_NAME', 'nesop_store');
define('DB_USER', 'nesop_user');
define('DB_PASS', 'your_secure_password');

// Application Configuration
define('APP_NAME', 'NESOP Store');
define('APP_URL', 'http://your-server-ip');
define('APP_ENV', 'development'); // 'development' or 'production'

// Email Configuration
define('SMTP_HOST', 'smtp.example.com');
define('SMTP_PORT', 587);
define('SMTP_USER', 'your-email@example.com');
define('SMTP_PASS', 'your-email-password');
define('SMTP_FROM', 'your-email@example.com');
define('SMTP_FROM_NAME', 'NESOP Store');
define('ADMIN_EMAIL', 'admin@example.com');

// Security Configuration
define('SESSION_LIFETIME', 3600); // 1 hour in seconds
define('PASSWORD_HASH_COST', 12); // For password_hash()

// Error Reporting
if (APP_ENV === 'development') {
    error_reporting(E_ALL);
    ini_set('display_errors', 1);
} else {
    error_reporting(0);
    ini_set('display_errors', 0);
}

// Logging Configuration
define('LOG_PATH', __DIR__ . '/../logs');
define('LOG_LEVEL', 'debug'); // 'debug', 'info', 'warning', 'error'

// File Upload Configuration
define('UPLOAD_PATH', __DIR__ . '/../public/uploads');
define('MAX_FILE_SIZE', 5 * 1024 * 1024); // 5MB
define('ALLOWED_FILE_TYPES', ['jpg', 'jpeg', 'png', 'gif']);

// Currency Configuration
define('CURRENCY_SYMBOL', '₪');
define('CURRENCY_NAME', 'NESOP Points'); 