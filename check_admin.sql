-- Connect to the database
USE nesop_store;

-- Show all users
SELECT id, username, email, role, balance, created_at 
FROM users;

-- Show specific admin user
SELECT id, username, email, role, balance, created_at 
FROM users 
WHERE username = 'admin'; 