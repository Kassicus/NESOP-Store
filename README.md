# NESOP Store

# Project Structure

```
NESOP-Store/
│
├── index.html              # Main entry point (storefront, login, etc.)
├── cart.html               # Cart and checkout page
├── styles/
│   └── main.css            # Main stylesheet
├── scripts/
│   ├── auth.js             # Authentication logic
│   ├── store.js            # Storefront logic (load/display items)
│   ├── cart.js             # Cart and checkout logic
│   ├── csv.js              # CSV parsing/handling utilities
│   └── utils.js            # Shared utility functions
├── data/
│   ├── users.csv           # User credentials and balances
│   └── items.csv           # Store items
├── assets/
│   └── images/             # Product images, logo, etc.
├── README.md               # Project documentation
└── project_goal.md         # Your project goal/spec
```

# Getting Started

1. Create the folders and files as shown above.
2. Use the provided skeleton code in each file to get started.
3. Open `index.html` in your browser to begin development.
4. For now, CSV data will be simulated in JavaScript for demo purposes.

## Active Directory Integration

This project now supports Microsoft Active Directory (AD) authentication for user login and admin access. To enable AD integration:

1. Configure your AD server settings in `server.py`:
   - `LDAP_HOST`, `LDAP_BASE_DN`, `LDAP_USER_DN`, `LDAP_GROUP_DN`, `LDAP_USER_RDN_ATTR`, `LDAP_USER_LOGIN_ATTR`, `LDAP_BIND_USER_DN`, `LDAP_BIND_USER_PASSWORD`
2. The `/api/login` endpoint authenticates users against AD. If a user logs in for the first time, a local user record is created.
3. Admin status is determined by AD group membership (see `admin_group` in `server.py`).
4. The frontend login form now uses `/api/login` and stores admin status in `localStorage` as `nesop_user_admin`.
5. The admin panel checks `localStorage` for admin access.

**Note:** You must install the required dependencies (`python-ldap`, `flask-ldap3-login`) and have network access to your AD server.

- The registration page and self-service registration flow have been removed. All user management is now handled via Active Directory (AD) only.