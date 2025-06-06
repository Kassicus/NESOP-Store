<?php
echo "<h2>Testing API Endpoint</h2>";

// Test data
$data = [
    'username' => 'admin',
    'password' => 'admin123'
];

// Make the API request
$ch = curl_init('http://' . $_SERVER['HTTP_HOST'] . '/api/auth/login');
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
curl_setopt($ch, CURLOPT_POST, true);
curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($data));
curl_setopt($ch, CURLOPT_HTTPHEADER, [
    'Content-Type: application/json'
]);

// Get the response
$response = curl_exec($ch);
$httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);

echo "<h3>API Response:</h3>";
echo "HTTP Status Code: " . $httpCode . "<br>";
echo "Response Body:<br>";
echo "<pre>";
print_r(json_decode($response, true));
echo "</pre>";

// Check for errors
if (curl_errno($ch)) {
    echo "<h3>Curl Error:</h3>";
    echo curl_error($ch);
}

curl_close($ch); 