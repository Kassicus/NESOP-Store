# Active Directory Configuration Template

## Required Information for Real AD Integration

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
AD Server URL: ldap://your-dc.company.com (or ldaps:// for SSL)
AD Domain: company.com
Service Account DN: CN=nesop_service,OU=Service Accounts,DC=company,DC=com
Service Account Password: [your-password]
User Base DN: OU=Users,DC=company,DC=com
Admin Group DN: CN=NESOP_Admins,OU=Groups,DC=company,DC=com
```

### Environment Variables (.env.production)
```env
AD_ENABLED=true
AD_USE_MOCK=false
AD_SERVER_URL=ldap://your-dc.company.com
AD_DOMAIN=company.com
AD_BIND_DN=CN=nesop_service,OU=Service Accounts,DC=company,DC=com
AD_BIND_PASSWORD=your-service-account-password
AD_USER_BASE_DN=OU=Users,DC=company,DC=com
AD_ADMIN_GROUP=CN=NESOP_Admins,OU=Groups,DC=company,DC=com
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

### Issue: "Admin detection not working"
- Check Admin Group DN is correct
- Verify users are members of admin group
- Check group membership format
- Verify service account can read group membership

## Final Checklist

Before deployment:
- [ ] All required information collected
- [ ] Service account created and tested
- [ ] Admin group created and populated
- [ ] Network connectivity verified
- [ ] Configuration values ready for deployment script

After deployment:
- [ ] Application starts successfully
- [ ] AD connectivity works
- [ ] User authentication works
- [ ] Admin detection works
- [ ] Fallback admin still accessible 