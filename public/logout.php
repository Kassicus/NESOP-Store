<?php
require_once __DIR__ . '/../config/config.php';
require_once __DIR__ . '/../src/utils/Auth.php';

session_start();

Auth::getInstance()->logout();

$_SESSION['flash_message'] = 'You have been successfully logged out.';
$_SESSION['flash_type'] = 'success';

header('Location: ' . APP_URL . '/login.php');
exit; 