<?php
echo "<h2>Testing API Endpoint</h2>";

// Enable error reporting
error_reporting(E_ALL);
ini_set('display_errors', 1);

// Test data
$data = [
    'username' => 'admin',
    'password' => 'admin123'
];

echo "<h3>1. Configuration Check:</h3>";
echo "Server Host: " . $_SERVER['HTTP_HOST'] . "<br>";
echo "API URL: https://" . $_SERVER['HTTP_HOST'] . "/api/auth/login<br>";
echo "Request Data: <pre>" . json_encode($data, JSON_PRETTY_PRINT) . "</pre><br>";

// Make the API request
$ch = curl_init('https://' . $_SERVER['HTTP_HOST'] . '/api/auth/login');
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
curl_setopt($ch, CURLOPT_POST, true);
curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($data));
curl_setopt($ch, CURLOPT_HTTPHEADER, [
    'Content-Type: application/json'
]);
curl_setopt($ch, CURLOPT_TIMEOUT, 10); // 10 second timeout
curl_setopt($ch, CURLOPT_CONNECTTIMEOUT, 5); // 5 second connection timeout
curl_setopt($ch, CURLOPT_VERBOSE, true);
curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, false); // For testing only - remove in production
curl_setopt($ch, CURLOPT_SSL_VERIFYHOST, 0); // For testing only - remove in production

// Create a temporary file handle for CURL debug output
$verbose = fopen('php://temp', 'w+');
curl_setopt($ch, CURLOPT_STDERR, $verbose);

echo "<h3>2. Making API Request...</h3>";

// Get the response
$response = curl_exec($ch);
$httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);

echo "<h3>3. Response Information:</h3>";
echo "HTTP Status Code: " . $httpCode . "<br>";

// Get CURL debug information
rewind($verbose);
$verboseLog = stream_get_contents($verbose);
echo "<h3>4. CURL Debug Information:</h3>";
echo "<pre>" . htmlspecialchars($verboseLog) . "</pre>";

// Check for errors
if (curl_errno($ch)) {
    echo "<h3>5. CURL Error:</h3>";
    echo "Error Code: " . curl_errno($ch) . "<br>";
    echo "Error Message: " . curl_error($ch) . "<br>";
}

// Check if we got a response
if ($response !== false) {
    echo "<h3>6. Response Body:</h3>";
    echo "<pre>";
    print_r(json_decode($response, true));
    echo "</pre>";
} else {
    echo "<h3>6. No Response Received</h3>";
}

curl_close($ch);
fclose($verbose); 