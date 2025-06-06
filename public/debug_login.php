<?php
require_once __DIR__ . '/../config/config.php';
require_once __DIR__ . '/../src/utils/Database.php';

echo "<h2>Debug Login Information</h2>";

try {
    $db = Database::getInstance();
    
    // 1. Check if admin user exists
    $admin = $db->query(
        "SELECT id, username, email, password_hash, role FROM users WHERE username = 'admin'"
    )->fetch();
    
    echo "<h3>1. Admin User Check:</h3>";
    if ($admin) {
        echo "Admin user found:<br>";
        echo "ID: " . $admin['id'] . "<br>";
        echo "Username: " . $admin['username'] . "<br>";
        echo "Email: " . $admin['email'] . "<br>";
        echo "Role: " . $admin['role'] . "<br>";
        echo "Password Hash: " . $admin['password_hash'] . "<br><br>";
        
        // 2. Test password verification
        $test_password = 'admin123';
        $verify = password_verify($test_password, $admin['password_hash']);
        
        echo "<h3>2. Password Verification Test:</h3>";
        echo "Testing password 'admin123': " . ($verify ? "SUCCESS" : "FAILED") . "<br><br>";
        
        // 3. Create new password hash for comparison
        $new_hash = password_hash($test_password, PASSWORD_BCRYPT, ['cost' => 12]);
        
        echo "<h3>3. New Password Hash:</h3>";
        echo "New hash for 'admin123': " . $new_hash . "<br><br>";
        
        // 4. Update admin password if verification failed
        if (!$verify) {
            echo "<h3>4. Updating Admin Password:</h3>";
            $db->query(
                "UPDATE users SET password_hash = ? WHERE username = 'admin'",
                [$new_hash]
            );
            echo "Admin password has been updated to 'admin123'<br>";
        }
    } else {
        echo "Admin user not found! Creating new admin user...<br>";
        
        // Create new admin user
        $password = 'admin123';
        $hash = password_hash($password, PASSWORD_BCRYPT, ['cost' => 12]);
        
        $db->query(
            "INSERT INTO users (username, email, password_hash, role) VALUES (?, ?, ?, ?)",
            ['admin', 'admin@example.com', $hash, 'admin']
        );
        
        echo "New admin user created with password 'admin123'<br>";
    }
    
    // 5. Check database connection
    echo "<h3>5. Database Connection Test:</h3>";
    echo "Database connection successful<br>";
    echo "Database name: " . DB_NAME . "<br>";
    echo "Database user: " . DB_USER . "<br>";
    
} catch (Exception $e) {
    echo "<h3>Error:</h3>";
    echo $e->getMessage();
} 