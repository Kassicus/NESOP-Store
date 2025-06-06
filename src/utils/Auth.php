<?php
/**
 * Authentication Utility Class
 * 
 * Handles user authentication and session management
 */
class Auth {
    private static $instance = null;
    private $db;

    private function __construct() {
        $this->db = Database::getInstance();
    }

    public static function getInstance() {
        if (self::$instance === null) {
            self::$instance = new self();
        }
        return self::$instance;
    }

    /**
     * Attempt to log in a user
     */
    public function login($username, $password) {
        try {
            $result = $this->db->query(
                "SELECT id, username, password_hash, role, balance FROM users WHERE username = ? AND is_active = TRUE",
                [$username]
            )->fetch();

            if ($result && password_verify($password, $result['password_hash'])) {
                // Update last login
                $this->db->query(
                    "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?",
                    [$result['id']]
                );

                // Set session variables
                $_SESSION['user_id'] = $result['id'];
                $_SESSION['username'] = $result['username'];
                $_SESSION['role'] = $result['role'];
                $_SESSION['balance'] = $result['balance'];

                return true;
            }
            return false;
        } catch (Exception $e) {
            error_log("Login error: " . $e->getMessage());
            return false;
        }
    }

    /**
     * Log out the current user
     */
    public function logout() {
        session_destroy();
        return true;
    }

    /**
     * Check if user is logged in
     */
    public function isLoggedIn() {
        return isset($_SESSION['user_id']);
    }

    /**
     * Check if user is admin
     */
    public function isAdmin() {
        return isset($_SESSION['role']) && $_SESSION['role'] === 'admin';
    }

    /**
     * Get current user's ID
     */
    public function getUserId() {
        return $_SESSION['user_id'] ?? null;
    }

    /**
     * Get current user's username
     */
    public function getUsername() {
        return $_SESSION['username'] ?? null;
    }

    /**
     * Get current user's balance
     */
    public function getBalance() {
        return $_SESSION['balance'] ?? 0;
    }

    /**
     * Update user's balance in session
     */
    public function updateBalance($newBalance) {
        $_SESSION['balance'] = $newBalance;
    }

    /**
     * Require user to be logged in
     */
    public function requireLogin() {
        if (!$this->isLoggedIn()) {
            $_SESSION['flash_message'] = 'Please log in to access this page.';
            $_SESSION['flash_type'] = 'warning';
            header('Location: ' . APP_URL . '/login.php');
            exit;
        }
    }

    /**
     * Require user to be admin
     */
    public function requireAdmin() {
        $this->requireLogin();
        if (!$this->isAdmin()) {
            $_SESSION['flash_message'] = 'You do not have permission to access this page.';
            $_SESSION['flash_type'] = 'error';
            header('Location: ' . APP_URL . '/dashboard.php');
            exit;
        }
    }
} 