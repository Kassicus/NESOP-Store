<?php
require_once __DIR__ . '/../config.php';

// Validate request method
validateMethod('POST');

// Get and validate request data
$data = getRequestBody();
validateRequired($data, ['username', 'password']);

try {
    $db = Database::getInstance();
    
    // Get user from database
    $result = $db->query(
        "SELECT id, username, password_hash, role, balance FROM users WHERE username = ? AND is_active = TRUE",
        [$data['username']]
    )->fetch();

    // Verify password
    if ($result && password_verify($data['password'], $result['password_hash'])) {
        // Update last login
        $db->query(
            "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?",
            [$result['id']]
        );

        // Remove sensitive data
        unset($result['password_hash']);

        // Send success response
        sendResponse([
            'message' => 'Login successful',
            'user' => $result
        ]);
    } else {
        sendError('Invalid username or password', 401);
    }
} catch (Exception $e) {
    error_log("Login error: " . $e->getMessage());
    sendError('An error occurred during login', 500);
} 