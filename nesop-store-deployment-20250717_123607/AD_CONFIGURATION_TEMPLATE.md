# Active Directory Configuration Template

## Admin Management

**Important:** Admin permissions are now managed locally within the application, not through AD groups. This provides several benefits:

✅ **Advantages:**
- No AD group configuration required
- Flexible admin permission management
- Works with any AD setup (simple bind or service account)
- Admins can be promoted/demoted through the admin panel
- No dependency on AD group membership changes

🔧 **How it works:**
1. New AD users are imported as regular users (not admin)
2. Use the admin panel to promote users to admin status
3. Admin permissions are stored locally in the application database
4. Fallback admin account is always available for emergency access

## Authentication Modes

The NESOP Store supports two AD authentication modes:

### 1. Simple Bind Mode (Recommended for Basic Setup)
**Like PhotoPrism** - No service account needed, simple setup

✅ **Advantages:**
- No service account required
- Simpler setup process
- Users authenticate with their own credentials
- Works with most AD environments out of the box

❌ **Limitations:**
- Limited user search capabilities in admin panel
- Group membership checking requires additional search
- No user discovery/browsing features

**Best for:** Small teams, simple deployments, when you don't want to manage service accounts

### 2. Service Account Mode (Full Features)
**Traditional approach** - Uses dedicated service account

✅ **Advantages:**
- Full user search and discovery in admin panel
- Easy group membership checking
- Rich user information display
- Admin can browse and manage AD users

❌ **Requirements:**
- Requires dedicated service account
- More complex setup
- Need to manage service account credentials

**Best for:** Larger deployments, when you need user management features

---

## Simple Bind Mode Configuration

### Quick Setup (No Service Account)
```bash
# Run deployment configuration
python3 deploy_config.py

# Select options:
# 1. Enable AD integration: Y
# 2. Use mock AD: N
# 3. Authentication mode: 1 (Simple bind)
# 4. Choose DN pattern (usually option 1)
# 5. Provide domain and server details
```

### Required Information
```
AD Server: your-dc.yourdomain.com
Domain: yourdomain.com
User Base DN: OU=Users,DC=yourdomain,DC=com (optional)
```

**Note:** Admin permissions are now managed locally within the application. New AD users are imported as regular users and can be promoted to admin through the admin panel. No AD group configuration is required.

### DN Pattern Options
1. **{username}@{domain}** - Most common (e.g., jsmith@company.com)
2. **{domain}\\{username}** - Windows style (e.g., COMPANY\\jsmith)
3. **CN={username},{user_base_dn}** - Distinguished name style
4. **Custom pattern** - For unique environments

### Environment Variables (.env.production)
```env
AD_ENABLED=true
AD_USE_MOCK=false
AD_SIMPLE_BIND_MODE=true
AD_SERVER_URL=ldap://your-dc.yourdomain.com
AD_DOMAIN=yourdomain.com
AD_USER_DN_PATTERN={username}@{domain}
AD_USER_BASE_DN=OU=Users,DC=yourdomain,DC=com
AD_ADMIN_GROUP=CN=NESOP_Admins,OU=Groups,DC=yourdomain,DC=com
AD_USE_SSL=true
AD_PORT=636
AD_TIMEOUT=10
```

### Testing Simple Bind
```bash
# Test with any domain user
# Username: jsmith
# Password: [user's password]
# No service account needed!
```

---

## Service Account Mode Configuration

### Required Information for Real AD Integration

### 1. Active Directory Server Information
```
AD Server (Domain Controller):
- Primary DC: ____________________
- Secondary DC (optional): ____________________
- Port: 636 (LDAPS) or 389 (LDAP)
- Use SSL/TLS: Yes (recommended) / No
```

### 2. Domain Information
```
Domain Name: ____________________
Example: company.com, mydomain.local
```

### 3. Service Account Information
```
Service Account Name: ____________________
Service Account Password: ____________________
Service Account DN: CN=____________________,OU=Service Accounts,DC=____________________,DC=____________________

Example: CN=nesop_service,OU=Service Accounts,DC=company,DC=com
```

### 4. User Search Configuration
```
User Base DN: OU=____________________,DC=____________________,DC=____________________
Example: OU=Users,DC=company,DC=com
```

### 5. Admin Group Configuration
```
Admin Group Name: ____________________
Admin Group DN: CN=____________________,OU=____________________,DC=____________________,DC=____________________

Example: CN=NESOP_Admins,OU=Groups,DC=company,DC=com
```

## Service Account Setup Instructions

### 1. Create Service Account in AD
1. Open "Active Directory Users and Computers"
2. Navigate to your Service Accounts OU (or Users)
3. Right-click → New → User
4. Create user with name like "nesop_service"
5. Set a strong password
6. Check "Password never expires" (recommended for service accounts)
7. Uncheck "User must change password at next logon"

### 2. Grant Permissions
The service account needs:
- **Read** permission on the User Base DN
- **Read** permission on the Admin Group
- **No write permissions needed** (read-only access)

### 3. Admin Group Setup
1. Create a new security group (e.g., "NESOP_Admins")
2. Add users who should have admin access to this group
3. Note the full DN of the group

## Testing Your AD Configuration

### 1. Test LDAP Connectivity
From your server, test connection to your domain controller:
```bash
# Test basic connectivity
telnet your-dc.company.com 636  # For LDAPS
telnet your-dc.company.com 389  # For LDAP

# Test with ldapsearch (if available)
ldapsearch -x -H ldap://your-dc.company.com -D "CN=nesop_service,OU=Service Accounts,DC=company,DC=com" -W -b "OU=Users,DC=company,DC=com" "(sAMAccountName=*)"
```

### 2. Validate Service Account
Ensure the service account can:
- Bind to the LDAP server
- Search the user base DN
- Read user attributes (sAMAccountName, displayName, mail, memberOf)

## Configuration for deploy_config.py

When you run the deployment configuration, use these settings:

### Interactive Setup Responses
```
Enable AD integration? Y
Use mock AD for testing? N
Authentication mode: 1 (Simple bind) or 2 (Service account)

# For Simple Bind Mode:
AD Server URL: ldap://your-dc.company.com (or ldaps:// for SSL)
AD Domain: company.com
Choose DN pattern: 1 (usually {username}@{domain})
User Base DN: OU=Users,DC=company,DC=com
Admin Group DN: CN=NESOP_Admins,OU=Groups,DC=company,DC=com

# For Service Account Mode:
AD Server URL: ldap://your-dc.company.com (or ldaps:// for SSL)
AD Domain: company.com
Service Account DN: CN=nesop_service,OU=Service Accounts,DC=company,DC=com
Service Account Password: [your-password]
User Base DN: OU=Users,DC=company,DC=com
Admin Group DN: CN=NESOP_Admins,OU=Groups,DC=company,DC=com
```

### Environment Variables (.env.production)

#### Simple Bind Mode
```env
AD_ENABLED=true
AD_USE_MOCK=false
AD_SIMPLE_BIND_MODE=true
AD_SERVER_URL=ldap://your-dc.company.com
AD_DOMAIN=company.com
AD_USER_DN_PATTERN={username}@{domain}
AD_USER_BASE_DN=OU=Users,DC=company,DC=com
AD_ADMIN_GROUP=  # Optional: Leave empty to manage admin permissions locally
AD_USE_SSL=true
AD_PORT=636
AD_TIMEOUT=10
```

#### Service Account Mode
```env
AD_ENABLED=true
AD_USE_MOCK=false
AD_SIMPLE_BIND_MODE=false
AD_SERVER_URL=ldap://your-dc.company.com
AD_DOMAIN=company.com
AD_BIND_DN=CN=nesop_service,OU=Service Accounts,DC=company,DC=com
AD_BIND_PASSWORD=your-service-account-password
AD_USER_BASE_DN=OU=Users,DC=company,DC=com
AD_ADMIN_GROUP=  # Optional: Leave empty to manage admin permissions locally
AD_USE_SSL=true
AD_PORT=636
AD_TIMEOUT=10
```

## Security Considerations

### 1. Service Account Security
- Use a dedicated service account (don't use a user account)
- Set a strong password
- Consider password rotation policy
- Monitor service account usage

### 2. Network Security
- Deploy on internal network only
- Use LDAPS (SSL/TLS) if possible
- Restrict server access to authorized personnel
- Consider firewall rules between server and DC

### 3. Permissions
- Grant minimum required permissions
- Regularly review group memberships
- Monitor admin group changes

## Testing Steps

### 1. Before Deployment
- [ ] Service account created and configured
- [ ] Admin group created and populated
- [ ] Network connectivity verified
- [ ] LDAP/LDAPS connectivity tested

### 2. After Deployment
- [ ] AD user search works in admin panel
- [ ] AD authentication works for test users
- [ ] Admin users have admin access
- [ ] Non-admin users have regular access
- [ ] Fallback admin still works

## Common Issues and Solutions

### Issue: "Could not connect to AD server"
- Check server hostname/IP
- Verify port (389 for LDAP, 636 for LDAPS)
- Check firewall rules
- Verify network connectivity

### Issue: "Authentication failed"
- Check service account credentials
- Verify service account is not locked
- Check service account permissions
- Verify DN format is correct

### Issue: "User not found"
- Check User Base DN is correct
- Verify user exists in specified OU
- Check LDAP filters
- Verify service account has read access

### Issue: "Admin permissions not working"
- Admin permissions are managed locally through the application
- Use the admin panel to promote users to admin status
- Fallback admin account can always be used: fallback_admin / ChangeMe123!

## Final Checklist

Before deployment:
- [ ] All required information collected
- [ ] Service account created and tested (for service account mode)
- [ ] Network connectivity verified
- [ ] Configuration values ready for deployment script

After deployment:
- [ ] Application starts successfully
- [ ] AD connectivity works
- [ ] User authentication works
- [ ] Admin panel accessible for user management
- [ ] Fallback admin still accessible (fallback_admin / ChangeMe123!) 