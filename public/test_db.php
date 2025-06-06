<?php
require_once __DIR__ . '/../config/config.php';
require_once __DIR__ . '/../src/utils/Database.php';

try {
    $db = Database::getInstance();
    echo "Database connection successful!";
} catch (Exception $e) {
    echo "Database connection failed: " . $e->getMessage();
} 