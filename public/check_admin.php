<?php
require_once __DIR__ . '/../config/config.php';
require_once __DIR__ . '/../src/utils/Database.php';

try {
    $db = Database::getInstance();
    
    // Query to get all users
    $users = $db->query("SELECT id, username, email, role, balance, created_at FROM users")->fetchAll();
    
    echo "<h2>Users in Database:</h2>";
    echo "<pre>";
    print_r($users);
    echo "</pre>";
    
} catch (Exception $e) {
    echo "Error: " . $e->getMessage();
} 