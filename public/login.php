<?php
require_once __DIR__ . '/../config/config.php';
require_once __DIR__ . '/../src/utils/Database.php';
require_once __DIR__ . '/../src/utils/Auth.php';

session_start();

// Redirect if already logged in
if (Auth::getInstance()->isLoggedIn()) {
    header('Location: ' . APP_URL . '/dashboard.php');
    exit;
}

$error = '';

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $username = $_POST['username'] ?? '';
    $password = $_POST['password'] ?? '';

    if (empty($username) || empty($password)) {
        $error = 'Please enter both username and password.';
    } else {
        if (Auth::getInstance()->login($username, $password)) {
            header('Location: ' . APP_URL . '/dashboard.php');
            exit;
        } else {
            $error = 'Invalid username or password.';
        }
    }
}

// Start output buffering
ob_start();
?>

<div class="form-container">
    <h2>Login</h2>
    <?php if ($error): ?>
        <div class="flash-message error">
            <?= htmlspecialchars($error) ?>
        </div>
    <?php endif; ?>
    
    <form method="POST" action="">
        <div class="form-group">
            <label for="username">Username</label>
            <input type="text" id="username" name="username" required>
        </div>
        
        <div class="form-group">
            <label for="password">Password</label>
            <input type="password" id="password" name="password" required>
        </div>
        
        <button type="submit" class="btn btn-block">Login</button>
    </form>
</div>

<?php
$content = ob_get_clean();
require_once __DIR__ . '/../src/views/layouts/main.php'; 