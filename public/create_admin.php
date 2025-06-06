<?php
require_once __DIR__ . '/../config/config.php';
require_once __DIR__ . '/../src/utils/Database.php';

try {
    $db = Database::getInstance();
    
    // Check if admin already exists
    $admin = $db->query(
        "SELECT id FROM users WHERE username = 'admin'"
    )->fetch();
    
    if ($admin) {
        echo "Admin user already exists!";
        exit;
    }
    
    // Create admin user
    $password = 'admin123'; // You can change this
    $hash = password_hash($password, PASSWORD_BCRYPT, ['cost' => 12]);
    
    $db->query(
        "INSERT INTO users (username, email, password_hash, role) VALUES (?, ?, ?, ?)",
        ['admin', 'admin@example.com', $hash, 'admin']
    );
    
    echo "Admin user created successfully!<br>";
    echo "Username: admin<br>";
    echo "Password: " . $password;
    
} catch (Exception $e) {
    echo "Error: " . $e->getMessage();
} 