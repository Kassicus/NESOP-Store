# NESOP Store

A comprehensive Flask-based web application for internal organization merchandise sales with Active Directory integration, admin management, and automated deployment capabilities.

## Overview

The NESOP Store is an internal e-commerce platform designed for organizations to sell merchandise to employees using their internal Active Directory credentials. The system features user authentication via AD/LDAP, inventory management, order processing, email notifications, and comprehensive administrative tools.

## Features

### Core Functionality
- **Product Catalog**: Browse and search merchandise with image uploads
- **Shopping Cart**: Add/remove items with quantity tracking
- **User Accounts**: Balance tracking and purchase history
- **Order Processing**: Streamlined checkout and fulfillment workflow

### Authentication & User Management
- **Active Directory Integration**: LDAP-based authentication with AD user sync
- **Local Admin Management**: Admin permissions managed through admin panel
- **User Registration**: New user registration with email validation
- **Fallback Authentication**: Emergency admin access when AD is unavailable

### Administrative Features
- **Admin Dashboard**: Overview of sales, inventory, and user activity
- **Inventory Management**: Add/edit/remove products with image uploads
- **User Management**: View and manage user accounts and permissions
- **Transaction Management**: Track orders and process fulfillment
- **Email Integration**: Automated order notifications and fulfillment alerts

### Technical Features
- **SQLite Database**: Structured data storage with migration support
- **File Upload Management**: Product image handling with proper permissions
- **Email Integration**: SMTP integration for order notifications
- **Deployment Automation**: Automated packaging and deployment system
- **Update Management**: Incremental updates with rollback capability
- **Configuration Management**: Comprehensive config system for all settings

## Architecture

### Backend (Flask Application)
```
NESOP-Store/
├── server.py                    # Main Flask application
├── db_utils.py                  # Database operations and utilities
├── ad_utils.py                  # Active Directory integration
├── config.py                    # Configuration management
├── email_utils.py               # Email notification system
└── wsgi.py                      # Production WSGI configuration
```

### Frontend (Web Interface)
```
├── index.html                   # Main storefront and login
├── cart.html                    # Shopping cart and checkout
├── account.html                 # User account management
├── register.html                # New user registration
├── admin.html                   # Main admin panel
├── admin-dashboard.html         # Admin dashboard
├── admin-inventory.html         # Inventory management
├── admin-users.html             # User management
├── admin-transactions.html      # Transaction management
├── scripts/
│   ├── auth.js                  # Authentication logic
│   ├── store.js                 # Storefront functionality
│   ├── cart.js                  # Cart operations
│   ├── register.js              # Registration forms
│   └── utils.js                 # Shared utilities
└── styles/
    └── main.css                 # Application styling
```

### Assets & Data
```
├── assets/
│   ├── images/                  # Product images and uploads
│   ├── favicon/                 # Site icons
│   └── resources/               # Static resources
├── nesop_store.db               # SQLite database (development)
├── nesop_store_production.db    # SQLite database (production)
└── logs/
    └── nesop_store.log          # Application logs
```

### Deployment & Management
```
├── create_deployment_package.py # Creates full deployment packages
├── create_update_package.py     # Creates incremental update packages
├── deploy_config.py             # Deployment configuration wizard
├── update_manager.py            # Update application system
├── validate_deployment.py       # Deployment validation
├── validate_update.py           # Update validation
├── requirements.txt             # Python dependencies
└── README.md                    # This documentation
```

## Dependencies

- **Flask 2.3.3**: Web framework
- **ldap3 2.9.1**: Active Directory/LDAP integration
- **gunicorn 21.2.0**: Production WSGI server
- **supervisor 4.2.5**: Process management

## Installation & Deployment

### Quick Deployment

1. **Create Deployment Package**:
   ```bash
   python3 create_deployment_package.py
   ```

2. **Transfer to Server**:
   ```bash
   scp nesop-store-deployment-YYYYMMDD_HHMMSS.tar.gz user@server:/tmp/
   ```

3. **Deploy on Server**:
   ```bash
   tar -xzf nesop-store-deployment-YYYYMMDD_HHMMSS.tar.gz
   cd nesop-store-deployment-YYYYMMDD_HHMMSS
   python3 deploy_config.py
   sudo ./deploy.sh
   ```

### Manual Setup

1. **Install Dependencies**:
   ```bash
   pip3 install -r requirements.txt
   ```

2. **Configure Settings**:
   ```bash
   python3 deploy_config.py
   ```

3. **Initialize Database**:
   ```bash
   python3 -c "import db_utils; db_utils.init_database()"
   ```

4. **Run Development Server**:
   ```bash
   python3 server.py
   ```

## Configuration

### Active Directory Setup
Configure AD integration in `config.py` or via the deployment wizard:
- **Server**: Your AD/LDAP server address
- **Port**: LDAP port (usually 389 or 636 for LDAPS)
- **Base DN**: Organization's distinguished name
- **Service Account**: Account for AD queries
- **Security**: Enable LDAPS for production

### Email Configuration
Configure SMTP settings for order notifications:
- **Server**: Your organization's email server
- **Credentials**: Service account for sending emails
- **Recipients**: Fulfillment team email addresses

### Admin Access
- **Default Admin**: `fallback_admin / ChangeMe123!`
- **AD Users**: Import via admin panel, assign admin permissions
- **Local Management**: Admin permissions managed locally (not via AD groups)

## API Endpoints

### Public Routes
- `GET /` - Main storefront
- `POST /login` - User authentication
- `POST /register` - New user registration
- `GET /logout` - User logout

### User Routes
- `POST /purchase` - Process purchase
- `GET /user-data` - Get user information
- `POST /add-to-cart` - Add item to cart
- `POST /update-cart-quantity` - Update cart quantities

### Admin Routes
- `GET /admin` - Admin panel
- `POST /admin/add-item` - Add inventory item
- `POST /admin/upload-image` - Upload product image
- `GET /admin/get-items` - Get inventory data
- `GET /admin/get-users` - Get user data
- `GET /admin/get-transactions` - Get transaction data

## Database Schema

### Users Table
- User authentication and profile information
- AD integration fields
- Balance and permission tracking

### Items Table
- Product inventory and details
- Image references and pricing
- Stock tracking

### Transactions Table
- Purchase history and order tracking
- User and item relationships
- Order status and fulfillment

## Security Features

- **LDAP Authentication**: Secure AD integration
- **Session Management**: Flask session handling
- **File Upload Security**: Validated image uploads with permission management
- **Admin Access Control**: Role-based admin functionality
- **Input Validation**: Server-side validation for all user inputs
- **Logging**: Comprehensive audit logging for all operations

## Update Management

### Creating Updates
```bash
# Standard update package
python3 create_update_package.py

# Custom update with specific files
python3 create_update_package.py --files server.py admin.html
```

### Applying Updates
```bash
# On production server
python3 update_manager.py apply update-package.tar.gz

# Validate update
python3 validate_update.py
```

## Troubleshooting

### Common Issues
1. **AD Connection Issues**: Check network connectivity and credentials
2. **File Upload Errors**: Verify directory permissions and ownership
3. **Database Errors**: Check SQLite file permissions and disk space
4. **Email Delivery**: Verify SMTP settings and network access

### Log Files
- Application logs: `logs/nesop_store.log`
- Check logs for detailed error information and debugging

## Development

### Project Structure
The application follows a modular structure with clear separation of concerns:
- **Database Layer**: `db_utils.py` handles all database operations
- **Authentication**: `ad_utils.py` manages AD integration
- **Configuration**: `config.py` centralizes all settings
- **Email**: `email_utils.py` handles notifications
- **Web Layer**: `server.py` contains Flask routes and business logic

### Adding Features
1. Update database schema in `db_utils.py`
2. Add backend logic to `server.py`
3. Create/modify frontend HTML and JavaScript
4. Update configuration in `config.py` if needed
5. Test thoroughly before deployment

## Support

For deployment issues, configuration questions, or feature requests, refer to:
- Application logs in `logs/nesop_store.log`
- Configuration files in the project root
- Admin panel for user and inventory management

## License

Internal use only - Architectural Nexus, INC