<?php
header('Content-Type: application/json');

// Basic response
echo json_encode([
    'status' => 'success',
    'message' => 'API is working',
    'timestamp' => date('Y-m-d H:i:s'),
    'server_info' => [
        'php_version' => PHP_VERSION,
        'server_software' => $_SERVER['SERVER_SOFTWARE'],
        'request_method' => $_SERVER['REQUEST_METHOD'],
        'is_https' => isset($_SERVER['HTTPS']) && $_SERVER['HTTPS'] === 'on',
        'protocol' => $_SERVER['SERVER_PROTOCOL'],
        'port' => $_SERVER['SERVER_PORT']
    ]
]); 