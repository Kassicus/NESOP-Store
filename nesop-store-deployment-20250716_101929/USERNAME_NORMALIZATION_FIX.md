# Username Normalization Fix - NESOP Store v1.0.5

## Problem Description

Previously, the NESOP Store could create duplicate users when someone logged in with different username formats:
- First login: `username@company.com` → Creates user `username@company.com`
- Second login: `username` → Creates user `username`

This resulted in two separate user accounts for the same person, causing confusion and data fragmentation.

## Solution

The application now normalizes usernames before storing them in the database:
- `username@company.com` → `username`
- `DOMAIN\username` → `username` 
- `username` → `username`

All usernames are normalized to lowercase and stripped of domain suffixes/prefixes.

## Changes Made

1. **Added username normalization function** in `ad_utils.py`:
   - `normalize_username()` function handles all username formats
   - Removes domain suffixes (@domain.com) and prefixes (DOMAIN\)
   - Converts to lowercase for consistency

2. **Updated authentication flow** in `server.py`:
   - Login function now uses normalized usernames for database operations
   - Still uses original username for AD authentication
   - Checks for existing users with normalized username

3. **Updated user creation** in `server.py`:
   - Registration endpoint uses normalized usernames
   - Admin user creation uses normalized usernames
   - Prevents duplicate user creation

## Migration Script

If you already have duplicate users in your system, run the migration script:

```bash
python3 migrate_username_normalization.py
```

### Migration Process

1. **Backup**: Creates automatic database backup before migration
2. **Detection**: Identifies groups of users with the same normalized username
3. **Merging**: Combines duplicate user data:
   - Keeps highest balance across all duplicates
   - Preserves admin status if any duplicate has it
   - Updates all related records (purchases, reviews)
   - Keeps earliest creation date
4. **Cleanup**: Removes duplicate user records

### Migration Safety

- **Automatic backup**: Database is backed up before migration
- **Transaction safety**: All changes are wrapped in a transaction
- **Confirmation required**: User must confirm before migration proceeds
- **Verification**: Checks for remaining duplicates after migration

## Usage Examples

### Before Fix
```
User logs in with: john@company.com → Database stores: john@company.com
User logs in with: john → Database stores: john
Result: Two separate users
```

### After Fix
```
User logs in with: john@company.com → Database stores: john
User logs in with: john → Database stores: john
Result: Same user account
```

## Deployment

1. Deploy the updated application
2. If you have existing users, run the migration script:
   ```bash
   python3 migrate_username_normalization.py
   ```
3. Test login with different username formats
4. Verify no duplicate users are created

## Version History

- **v1.0.5**: Username normalization fix
- **v1.0.4**: UI improvements for simple bind mode
- **v1.0.3**: AD configuration fixes
- **v1.0.2**: Uninstall script addition
- **v1.0.1**: Initial AD integration fixes

## Notes

- The migration script is safe to run multiple times
- AD authentication still works with original username formats
- Display names and user experience remain unchanged
- Only internal database storage is normalized 