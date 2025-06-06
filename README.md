# NESOP Store

A web-based store system for company staff to trade virtual currency for company merchandise.

## Project Overview
This is a web application that allows staff members to:
- Log in and check their account balance
- Browse and purchase company swag using virtual currency
- Receive order confirmations via email
- Administrators can manage user balances and inventory

## Technical Stack
- Frontend: HTML5, CSS3, JavaScript (Vanilla)
- Backend: PHP (for Apache2 server)
- Database: MariaDB
- Server: Apache2
- Email: SMTP for order notifications

## Setup Instructions

### Prerequisites
- Apache2 web server
- MariaDB
- PHP 7.4 or higher
- Git

### Installation Steps
1. Clone the repository:
   ```bash
   git clone [repository-url]
   cd NESOP-Store
   ```

2. Configure Apache2:
   - Ensure mod_rewrite is enabled
   - Point your Apache2 document root to the `public` directory
   - Configure virtual host settings

3. Set up MariaDB:
   - Create a new database
   - Import the initial schema from `database/schema.sql`

4. Configure the application:
   - Copy `config/config.example.php` to `config/config.php`
   - Update database credentials and other settings in `config/config.php`

5. Set up email configuration:
   - Configure SMTP settings in `config/config.php`

### Development
- The `public` directory contains all publicly accessible files
- The `src` directory contains the application source code
- The `database` directory contains database migrations and seeds
- The `tests` directory contains test files

## Project Structure
```
NESOP-Store/
├── public/           # Publicly accessible files
├── src/             # Application source code
│   ├── controllers/ # Request handlers
│   ├── models/      # Database models
│   ├── views/       # View templates
│   └── utils/       # Utility functions
├── database/        # Database migrations and seeds
├── tests/           # Test files
├── config/          # Configuration files
└── assets/          # Static assets (CSS, JS, images)
```

## Security
- All passwords are hashed using secure algorithms
- SQL injection prevention implemented
- XSS protection enabled
- CSRF protection in place
- Input validation on all forms

## License
[Your License Here]