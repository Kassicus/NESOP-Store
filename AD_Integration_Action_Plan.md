# Active Directory Integration Action Plan - NESOP Store

## Overview
This action plan outlines the steps to integrate Active Directory (AD) authentication with the NESOP-Store application while maintaining existing functionality and meeting all specified requirements.

## Requirements Summary
1. ✅ Integrate with Active Directory for user authentication (READ-ONLY)
2. ✅ Retain a single local admin account as fallback
3. ✅ Allow AD users to login and manage currency locally
4. ✅ Ability to assign administrator roles to AD users
5. ✅ Simple deployment configuration for internal server
6. ✅ No test AD environment - implement with fallback testing

## Current System Analysis
- **Authentication**: Simple username/password with SQLite storage
- **Database**: SQLite with `users` table (username, password, balance, is_admin)
- **Admin Panel**: Full CRUD operations for users and items
- **Backend**: Flask application with API endpoints
- **Frontend**: HTML/CSS/JavaScript with localStorage session management

## Implementation Phases

### Phase 1: Planning and Architecture (Task: ad_planning)
**Duration**: 1-2 days
**Description**: Design the hybrid authentication system

**Key Decisions**:
- Use python-ldap3 library for AD connectivity
- Implement dual authentication (local + AD)
- Extend database schema to support AD users
- Create configuration management system

**Deliverables**:
- Architecture design document
- Database schema changes
- Configuration requirements
- Security considerations

### Phase 2: Database Schema Updates (Task: db_schema_update)
**Duration**: 1 day
**Description**: Modify database to support mixed authentication

**Changes to `users` table**:
```sql
ALTER TABLE users ADD COLUMN user_type TEXT DEFAULT 'local';  -- 'local' or 'ad'
ALTER TABLE users ADD COLUMN ad_username TEXT;               -- AD samAccountName
ALTER TABLE users ADD COLUMN ad_domain TEXT;                -- AD domain
ALTER TABLE users ADD COLUMN last_ad_sync DATETIME;         -- Last AD sync
ALTER TABLE users ADD COLUMN is_active INTEGER DEFAULT 1;   -- Enable/disable users
```

**New table for AD configuration**:
```sql
CREATE TABLE ad_config (
    id INTEGER PRIMARY KEY,
    server_url TEXT NOT NULL,
    domain TEXT NOT NULL,
    bind_dn TEXT,
    bind_password TEXT,
    user_base_dn TEXT,
    user_filter TEXT,
    is_enabled INTEGER DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### Phase 3: AD Library Setup (Task: ad_library_setup)
**Duration**: 1 day
**Description**: Install and configure LDAP libraries

**Requirements**:
- Install `ldap3` library
- Configure AD connection settings
- Implement AD user search functionality
- Test AD connectivity

**Key Files**:
- `ad_utils.py` - AD connection and user management
- `requirements.txt` - Add ldap3 dependency

### Phase 4: Configuration Management (Task: config_management)
**Duration**: 1 day
**Description**: Create secure configuration system

**Configuration Areas**:
- AD server settings (server, domain, credentials)
- Local admin account settings
- Authentication priorities
- Security settings

**Files**:
- `config.py` - Configuration management
- `.env` file for sensitive settings
- `config_template.env` - Template for deployment

### Phase 5: Dual Authentication System (Task: dual_auth_system)
**Duration**: 2-3 days
**Description**: Implement hybrid local/AD authentication

**Authentication Flow**:
1. User enters credentials
2. Check if local admin account → authenticate locally
3. Check if user exists in local DB as AD user → authenticate via AD
4. If new user, attempt AD authentication → create local record if successful
5. Fall back to local authentication if AD unavailable

**Modified Files**:
- `server.py` - New authentication endpoints
- `auth.js` - Updated login flow
- `db_utils.py` - New user management functions

### Phase 6: AD User Management (Task: ad_user_management)
**Duration**: 2 days
**Description**: Create system for selective AD user import

**Features**:
- Browse AD users/groups
- Import selected users
- Sync user information
- Handle user deactivation

**New Admin Panel Features**:
- AD user browser
- Import/sync controls
- User activation/deactivation
- Role assignment for AD users

### Phase 7: Admin Panel Enhancement (Task: admin_panel_enhancement)
**Duration**: 2 days
**Description**: Enhance admin panel for AD user management

**New Admin Features**:
- AD configuration panel
- User type indicators (local/AD)
- Bulk user operations
- AD sync status and logs
- Role management for AD users

**Modified Files**:
- `admin.html` - New AD management sections
- `server.py` - New admin API endpoints
- `db_utils.py` - Enhanced user management functions

### Phase 8: Fallback Admin System (Task: fallback_admin_system)
**Duration**: 1 day
**Description**: Implement and test local admin fallback

**Fallback Features**:
- Dedicated local admin account (cannot be deleted)
- Emergency access when AD is unavailable
- Admin override capabilities
- Audit logging for fallback usage

**Security Measures**:
- Strong password requirements for local admin
- Account lockout protection
- Audit trail for admin actions
- Regular password rotation reminders

### Phase 9: Deployment Configuration (Task: deployment_config)
**Duration**: 1-2 days
**Description**: Prepare for production deployment

**Deployment Requirements**:
- Environment-specific configuration
- Database migration scripts
- WSGI configuration updates
- Service account setup for AD

**Files**:
- `deploy.sh` - Deployment script
- `migration.sql` - Database migration
- `wsgi.py` - Updated for production
- `systemd/nesop-store.service` - System service

### Phase 10: Final Testing (Task: testing_validation)
**Duration**: 1 day
**Description**: Test all authentication scenarios

**Testing Approach**:
- Mock AD responses for testing without AD environment
- Test local admin fallback
- Verify AD user authentication flow
- Test currency management for AD users

**Files**:
- `test_auth.py` - Authentication tests
- `mock_ad.py` - Mock AD responses for testing

### Phase 11: Deployment Guide (Task: deployment_guide)
**Duration**: 1 day
**Description**: Create simple deployment documentation

**Documentation**:
- Server requirements
- AD configuration steps
- Basic deployment procedures
- Troubleshooting guide

## Technical Specifications

### AD Integration Requirements
- **LDAP Protocol**: LDAP v3 over SSL/TLS
- **Authentication**: Simple bind authentication
- **User Attributes**: sAMAccountName, displayName, mail, memberOf
- **Group Support**: AD security groups for role assignment

### Database Changes
- Backward compatible schema updates
- Migration scripts for existing users
- Indexes for performance optimization

### Security Considerations
- Basic input validation and sanitization
- Secure AD service account (read-only)
- Simple audit logging for admin actions
- Local admin fallback protection

### Performance Considerations
- Connection pooling for AD queries
- Caching for frequently accessed AD data
- Asynchronous AD operations where possible
- Database query optimization

## Risk Assessment and Mitigation

### High Risk Items
1. **AD Server Unavailability**
   - Mitigation: Local admin fallback + cached credentials
2. **Database Migration Issues**
   - Mitigation: Full backup before migration + rollback procedures
3. **Security Vulnerabilities**
   - Mitigation: Code review + security testing + principle of least privilege

### Medium Risk Items
1. **Performance Degradation**
   - Mitigation: Connection pooling + caching + monitoring
2. **User Experience Issues**
   - Mitigation: Graceful error handling + clear feedback messages

## Success Criteria
- ✅ All existing functionality preserved
- ✅ AD users can authenticate successfully
- ✅ Local admin account works as fallback
- ✅ Selective AD user management operational
- ✅ Role assignment works for AD users
- ✅ System deployed successfully on server
- ✅ All security requirements met
- ✅ Performance meets current standards

## Next Steps
1. Review and approve this action plan
2. Set up development environment with AD test instance
3. Begin Phase 1 implementation
4. Regular progress reviews and adjustments as needed

This plan provides a structured approach to implementing AD integration while maintaining system reliability and meeting all specified requirements. 