#!/usr/bin/env python3
"""
Active Directory Utilities Module
Handles AD connections, authentication, and user management for NESOP Store.
Supports both simple LDAP bind and service account modes.
"""

import ldap3
import logging
import db_utils
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import ssl

# Setup logging
logger = logging.getLogger(__name__)

class ADConnectionError(Exception):
    """Exception raised when AD connection fails"""
    pass

class ADAuthenticationError(Exception):
    """Exception raised when AD authentication fails"""
    pass

class ADUserNotFoundError(Exception):
    """Exception raised when AD user is not found"""
    pass

class ActiveDirectoryManager:
    """Manages Active Directory connections and operations"""
    
    def __init__(self, use_mock=None):
        """
        Initialize AD Manager
        
        Args:
            use_mock (bool): Use mock AD responses for testing. If None, read from config.
        """
        # Get configuration from config system
        import config
        app_config = config.get_config()
        
        self.use_mock = use_mock if use_mock is not None else app_config.use_mock_ad
        self.connection = None
        self.config = None
        self.mock_users = self._create_mock_users()
        
        # Store app config for later use
        self.app_config = app_config
        
        # Simple bind mode configuration
        self.simple_bind_mode = getattr(app_config.ad_config, 'simple_bind_mode', False)
        self.user_dn_pattern = getattr(app_config.ad_config, 'user_dn_pattern', '{username}@{domain}')
        
    def _create_mock_users(self) -> Dict[str, Dict]:
        """Create mock AD users for testing"""
        return {
            'jsmith': {
                'sAMAccountName': 'jsmith',
                'displayName': 'John Smith',
                'mail': 'john.smith@company.com',
                'memberOf': ['CN=Users,DC=company,DC=com', 'CN=IT,DC=company,DC=com'],
                'userPrincipalName': 'jsmith@company.com',
                'department': 'IT',
                'title': 'System Administrator',
                'enabled': True
            },
            'mjohnson': {
                'sAMAccountName': 'mjohnson',
                'displayName': 'Mary Johnson',
                'mail': 'mary.johnson@company.com',
                'memberOf': ['CN=Users,DC=company,DC=com', 'CN=HR,DC=company,DC=com'],
                'userPrincipalName': 'mjohnson@company.com',
                'department': 'HR',
                'title': 'HR Manager',
                'enabled': True
            },
            'bwilson': {
                'sAMAccountName': 'bwilson',
                'displayName': 'Bob Wilson',
                'mail': 'bob.wilson@company.com',
                'memberOf': ['CN=Users,DC=company,DC=com', 'CN=Sales,DC=company,DC=com'],
                'userPrincipalName': 'bwilson@company.com',
                'department': 'Sales',
                'title': 'Sales Representative',
                'enabled': True
            },
            'admin': {
                'sAMAccountName': 'admin',
                'displayName': 'Administrator',
                'mail': 'admin@company.com',
                'memberOf': ['CN=Users,DC=company,DC=com', 'CN=NESOP_Admins,DC=company,DC=com'],
                'userPrincipalName': 'admin@company.com',
                'department': 'IT',
                'title': 'System Administrator',
                'enabled': True
            }
        }
    
    def _construct_user_dn(self, username: str) -> str:
        """
        Construct user DN based on configured pattern
        
        Args:
            username (str): Username to construct DN for
            
        Returns:
            str: User DN
        """
        if self.simple_bind_mode:
            domain = self.app_config.ad_config.domain
            pattern = self.user_dn_pattern
            
            # Clean username - remove domain if already present to avoid duplication
            clean_username = username
            if f"@{domain}" in username:
                clean_username = username.split(f"@{domain}")[0]
            elif f"{domain}\\" in username:
                clean_username = username.split(f"{domain}\\")[1]
            
            # Support different DN patterns
            if pattern == '{username}@{domain}':
                return f"{clean_username}@{domain}"
            elif pattern == 'CN={username},{user_base_dn}':
                return f"CN={clean_username},{self.app_config.ad_config.user_base_dn}"
            elif pattern == '{domain}\\{username}':
                return f"{domain}\\{clean_username}"
            else:
                # Custom pattern - replace placeholders
                return pattern.format(
                    username=clean_username,
                    domain=domain,
                    user_base_dn=self.app_config.ad_config.user_base_dn
                )
        else:
            # Service account mode - need to search for user first
            user_info = self._search_user(username)
            return user_info.get('dn') if user_info else None
    
    def _get_ad_config(self) -> Optional[Dict]:
        """Get AD configuration from database"""
        try:
            config = db_utils.get_ad_config()
            if config:
                return {
                    'server_url': config[1],
                    'domain': config[2],
                    'bind_dn': config[3],
                    'bind_password': config[4],
                    'user_base_dn': config[5],
                    'user_filter': config[6],
                    'search_attributes': config[7],
                    'is_enabled': config[8],
                    'use_ssl': config[9],
                    'port': config[10],
                    'timeout': config[11]
                }
            return None
        except Exception as e:
            logger.error(f"Error getting AD config: {str(e)}")
            return None
    
    def _connect_to_ad(self) -> bool:
        """
        Establish connection to Active Directory
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        if self.use_mock:
            logger.info("Using mock AD connection")
            return True
            
        try:
            # Check if AD is enabled in app config
            if not self.app_config.ad_config.is_enabled:
                logger.warning("AD integration is disabled in configuration")
                return False
                
            # Try to get database config, fall back to app config
            self.config = self._get_ad_config()
            if not self.config:
                # Use app config as fallback
                self.config = {
                    'server_url': self.app_config.ad_config.server_url,
                    'domain': self.app_config.ad_config.domain,
                    'bind_dn': self.app_config.ad_config.bind_dn,
                    'bind_password': self.app_config.ad_config.bind_password,
                    'user_base_dn': self.app_config.ad_config.user_base_dn,
                    'user_filter': self.app_config.ad_config.user_filter,
                    'search_attributes': self.app_config.ad_config.search_attributes,
                    'is_enabled': self.app_config.ad_config.is_enabled,
                    'use_ssl': self.app_config.ad_config.use_ssl,
                    'port': self.app_config.ad_config.port,
                    'timeout': self.app_config.ad_config.timeout
                }
                logger.info("Using app configuration for AD settings")
            
            if not self.config['is_enabled']:
                logger.warning("AD integration is disabled")
                return False
            
            # Create server object with enhanced timeouts
            server = ldap3.Server(
                self.config['server_url'],
                port=self.config['port'],
                use_ssl=self.config['use_ssl'],
                get_info=ldap3.ALL,
                connect_timeout=self.config['timeout'],
                receive_timeout=self.config['timeout']
            )
            
            # Create connection with enhanced security
            self.connection = ldap3.Connection(
                server,
                user=self.config['bind_dn'],
                password=self.config['bind_password'],
                authentication=ldap3.SIMPLE,
                auto_bind=True,
                auto_referrals=False,  # Prevent automatic referral following
                read_only=True  # Read-only connection for security
            )
            
            logger.info(f"Successfully connected to AD server: {self.config['server_url']}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to AD: {str(e)}")
            raise ADConnectionError(f"Failed to connect to AD: {str(e)}")
    
    def authenticate_user_simple_bind(self, username: str, password: str) -> Tuple[bool, Optional[Dict]]:
        """
        Authenticate user using simple LDAP bind (like PhotoPrism)
        
        Args:
            username (str): Username to authenticate
            password (str): Password to authenticate with
            
        Returns:
            Tuple[bool, Optional[Dict]]: (success, user_info)
        """
        try:
            logger.info(f"Attempting simple bind authentication for user: {username}")
            
            # Log authentication attempt
            db_utils.log_ad_event(
                username=username,
                action='simple_bind_attempt',
                details=f'Attempting simple bind authentication for user: {username}'
            )
            
            if self.use_mock:
                return self._mock_authenticate_user(username, password)
            
            # Construct user DN
            user_dn = self._construct_user_dn(username)
            if not user_dn:
                logger.error(f"Could not construct DN for user: {username}")
                return False, None
            
            logger.info(f"Using DN for authentication: {user_dn}")
            
            # Create server connection with timeouts
            server = ldap3.Server(
                self.app_config.ad_config.server_url,
                port=self.app_config.ad_config.port,
                use_ssl=self.app_config.ad_config.use_ssl,
                get_info=ldap3.ALL,
                connect_timeout=5,  # 5 second connection timeout
                receive_timeout=5   # 5 second receive timeout
            )
            
            # Attempt direct bind with user credentials
            connection = ldap3.Connection(
                server,
                user=user_dn,
                password=password,
                authentication=ldap3.SIMPLE,
                auto_bind=False,
                auto_referrals=False,  # Prevent automatic referral following
                read_only=True  # Read-only connection for security
            )
            
            # Attempt authentication with proper error handling
            try:
                bind_result = connection.bind()
                
                if bind_result:
                    logger.info(f"Simple bind successful for user: {username}")
                    
                    # Create basic user info
                    user_info = {
                        'sAMAccountName': username,
                        'displayName': username,  # We don't have full info in simple bind
                        'mail': f"{username}@{self.app_config.ad_config.domain}",
                        'dn': user_dn,
                        'userPrincipalName': f"{username}@{self.app_config.ad_config.domain}",
                        'memberOf': [],  # Can't easily get group memberships in simple bind
                        'enabled': True
                    }
                    
                    # Try to get additional user info if possible
                    try:
                        # Search for user info using the authenticated connection
                        base_dn = self.app_config.ad_config.user_base_dn
                        search_filter = f"(sAMAccountName={username})"
                        
                        if connection.search(base_dn, search_filter, attributes=['displayName', 'mail', 'memberOf']):
                            if connection.entries:
                                entry = connection.entries[0]
                                user_info.update({
                                    'displayName': str(entry.displayName) if entry.displayName else username,
                                    'mail': str(entry.mail) if entry.mail else user_info['mail'],
                                    'memberOf': [str(group) for group in entry.memberOf] if entry.memberOf else []
                                })
                                logger.info(f"Retrieved additional user info for: {username}")
                    except Exception as e:
                        logger.warning(f"Could not retrieve additional user info for {username}: {e}")
                    
                    db_utils.log_ad_event(
                        username=username,
                        action='simple_bind_success',
                        details=f'Simple bind successful for user: {username}'
                    )
                    
                    connection.unbind()
                    return True, user_info
                else:
                    # Authentication failed - get specific error details
                    error_msg = connection.result.get('description', 'Invalid credentials')
                    logger.warning(f"Simple bind failed for user: {username} - {error_msg}")
                    db_utils.log_ad_event(
                        username=username,
                        action='simple_bind_failed',
                        details=f'Simple bind failed for user: {username}',
                        success=False,
                        error_message=error_msg
                    )
                    connection.unbind()
                    return False, None
                    
            except ldap3.core.exceptions.LDAPInvalidCredentialsResult:
                logger.warning(f"Simple bind failed - invalid credentials for user: {username}")
                db_utils.log_ad_event(
                    username=username,
                    action='simple_bind_failed',
                    details=f'Simple bind failed - invalid credentials for user: {username}',
                    success=False,
                    error_message='Invalid credentials'
                )
                connection.unbind()
                return False, None
            except ldap3.core.exceptions.LDAPException as e:
                logger.error(f"LDAP error during simple bind for user {username}: {str(e)}")
                db_utils.log_ad_event(
                    username=username,
                    action='simple_bind_error',
                    details=f'LDAP error during simple bind: {str(e)}',
                    success=False,
                    error_message=str(e)
                )
                connection.unbind()
                return False, None
                
        except Exception as e:
            logger.error(f"Simple bind authentication error for user {username}: {str(e)}")
            db_utils.log_ad_event(
                username=username,
                action='simple_bind_error',
                details=f'Simple bind error: {str(e)}',
                success=False,
                error_message=str(e)
            )
            return False, None
    
    def authenticate_user(self, username: str, password: str) -> Tuple[bool, Optional[Dict]]:
        """
        Authenticate user using configured method (simple bind or service account)
        
        Args:
            username (str): Username to authenticate
            password (str): Password to authenticate with
            
        Returns:
            Tuple[bool, Optional[Dict]]: (success, user_info)
        """
        if self.simple_bind_mode:
            return self.authenticate_user_simple_bind(username, password)
        else:
            return self.authenticate_user_service_account(username, password)
    
    def authenticate_user_service_account(self, username: str, password: str) -> Tuple[bool, Optional[Dict]]:
        """
        Authenticate user using service account method (original implementation)
        
        Args:
            username (str): Username to authenticate
            password (str): Password to authenticate with
            
        Returns:
            Tuple[bool, Optional[Dict]]: (success, user_info)
        """
        try:
            logger.info(f"Attempting service account authentication for user: {username}")
            
            # Log authentication attempt
            db_utils.log_ad_event(
                username=username,
                action='authentication_attempt',
                details=f'Attempting to authenticate user: {username}'
            )
            
            if self.use_mock:
                return self._mock_authenticate_user(username, password)
            
            # Connect to AD
            if not self._connect_to_ad():
                raise ADConnectionError("Could not connect to AD server")
            
            # Search for user
            user_info = self._search_user(username)
            if not user_info:
                db_utils.log_ad_event(
                    username=username,
                    action='authentication_failed',
                    details=f'User not found in AD: {username}',
                    success=False,
                    error_message='User not found'
                )
                return False, None
            
            # Attempt authentication
            user_dn = user_info.get('dn')
            if not user_dn:
                logger.error(f"No DN found for user: {username}")
                return False, None
            
            # Create new connection for authentication
            auth_connection = ldap3.Connection(
                self.connection.server,
                user=user_dn,
                password=password,
                authentication=ldap3.SIMPLE,
                auto_bind=False,
                auto_referrals=False,  # Prevent automatic referral following
                read_only=True  # Read-only connection for security
            )
            
            # Attempt authentication with proper error handling
            try:
                bind_result = auth_connection.bind()
                
                if bind_result:
                    logger.info(f"Successfully authenticated user: {username}")
                    db_utils.log_ad_event(
                        username=username,
                        action='authentication_success',
                        details=f'Successfully authenticated user: {username}'
                    )
                    auth_connection.unbind()
                    return True, user_info
                else:
                    # Authentication failed - get specific error details
                    error_msg = auth_connection.result.get('description', 'Invalid credentials')
                    logger.warning(f"Authentication failed for user: {username} - {error_msg}")
                    db_utils.log_ad_event(
                        username=username,
                        action='authentication_failed',
                        details=f'Invalid credentials for user: {username}',
                        success=False,
                        error_message=error_msg
                    )
                    auth_connection.unbind()
                    return False, None
                    
            except ldap3.core.exceptions.LDAPInvalidCredentialsResult:
                logger.warning(f"Authentication failed - invalid credentials for user: {username}")
                db_utils.log_ad_event(
                    username=username,
                    action='authentication_failed',
                    details=f'Authentication failed - invalid credentials for user: {username}',
                    success=False,
                    error_message='Invalid credentials'
                )
                auth_connection.unbind()
                return False, None
            except ldap3.core.exceptions.LDAPException as e:
                logger.error(f"LDAP error during authentication for user {username}: {str(e)}")
                db_utils.log_ad_event(
                    username=username,
                    action='authentication_error',
                    details=f'LDAP error during authentication: {str(e)}',
                    success=False,
                    error_message=str(e)
                )
                auth_connection.unbind()
                return False, None
                
        except Exception as e:
            logger.error(f"Authentication error for user {username}: {str(e)}")
            db_utils.log_ad_event(
                username=username,
                action='authentication_error',
                details=f'Authentication error: {str(e)}',
                success=False,
                error_message=str(e)
            )
            return False, None
        finally:
            if self.connection:
                self.connection.unbind()
                self.connection = None
    
    def _mock_authenticate_user(self, username: str, password: str) -> Tuple[bool, Optional[Dict]]:
        """Mock authentication for testing"""
        # Simple mock: accept any password for known users
        if username in self.mock_users:
            user_info = self.mock_users[username].copy()
            user_info['dn'] = f'CN={user_info["displayName"]},CN=Users,DC=company,DC=com'
            
            # Mock password validation (accept "password123" for any user)
            if password == "password123":
                logger.info(f"Mock authentication successful for user: {username}")
                return True, user_info
            else:
                logger.warning(f"Mock authentication failed for user: {username}")
                return False, None
        else:
            logger.warning(f"Mock user not found: {username}")
            return False, None
    
    def _search_user(self, username: str) -> Optional[Dict]:
        """
        Search for user in Active Directory
        
        Args:
            username (str): Username to search for
            
        Returns:
            Optional[Dict]: User information if found, None otherwise
        """
        try:
            if self.use_mock:
                return self.mock_users.get(username)
            
            if not self.connection:
                raise ADConnectionError("No AD connection available")
            
            # Build search filter
            search_filter = f"(&(sAMAccountName={username}){self.config['user_filter']})"
            
            # Search for user
            success = self.connection.search(
                search_base=self.config['user_base_dn'],
                search_filter=search_filter,
                attributes=self.config['search_attributes'].split(',')
            )
            
            if success and self.connection.entries:
                entry = self.connection.entries[0]
                user_info = {
                    'dn': str(entry.entry_dn),
                    'sAMAccountName': str(entry.sAMAccountName),
                    'displayName': str(entry.displayName) if hasattr(entry, 'displayName') else username,
                    'mail': str(entry.mail) if hasattr(entry, 'mail') else None,
                    'memberOf': [str(group) for group in entry.memberOf] if hasattr(entry, 'memberOf') else []
                }
                return user_info
            
            return None
            
        except Exception as e:
            logger.error(f"Error searching for user {username}: {str(e)}")
            return None
    
    def search_users(self, search_term: str = "*", limit: int = 50) -> List[Dict]:
        """
        Search for users in Active Directory
        
        Args:
            search_term (str): Search term (supports wildcards)
            limit (int): Maximum number of results to return
            
        Returns:
            List[Dict]: List of user information
        """
        try:
            if self.use_mock:
                return self._mock_search_users(search_term, limit)
            
            if not self._connect_to_ad():
                raise ADConnectionError("Could not connect to AD server")
            
            # Build search filter
            if search_term == "*":
                search_filter = self.config['user_filter']
            else:
                search_filter = f"(&(|(sAMAccountName=*{search_term}*)(displayName=*{search_term}*)){self.config['user_filter']})"
            
            # Search for users
            success = self.connection.search(
                search_base=self.config['user_base_dn'],
                search_filter=search_filter,
                attributes=self.config['search_attributes'].split(','),
                size_limit=limit
            )
            
            users = []
            if success and self.connection.entries:
                for entry in self.connection.entries:
                    user_info = {
                        'dn': str(entry.entry_dn),
                        'sAMAccountName': str(entry.sAMAccountName),
                        'displayName': str(entry.displayName) if hasattr(entry, 'displayName') else str(entry.sAMAccountName),
                        'mail': str(entry.mail) if hasattr(entry, 'mail') else None,
                        'memberOf': [str(group) for group in entry.memberOf] if hasattr(entry, 'memberOf') else []
                    }
                    users.append(user_info)
            
            logger.info(f"Found {len(users)} users matching '{search_term}'")
            return users
            
        except Exception as e:
            logger.error(f"Error searching users: {str(e)}")
            return []
        finally:
            if self.connection:
                self.connection.unbind()
                self.connection = None
    
    def _mock_search_users(self, search_term: str, limit: int) -> List[Dict]:
        """Mock user search for testing"""
        users = []
        for username, user_info in self.mock_users.items():
            if search_term == "*" or search_term.lower() in username.lower() or search_term.lower() in user_info['displayName'].lower():
                user_copy = user_info.copy()
                user_copy['dn'] = f'CN={user_copy["displayName"]},CN=Users,DC=company,DC=com'
                users.append(user_copy)
                
                if len(users) >= limit:
                    break
        
        logger.info(f"Mock search found {len(users)} users matching '{search_term}'")
        return users
    
    def test_connection(self) -> Dict:
        """
        Test AD connection
        
        Returns:
            Dict: Connection test results
        """
        try:
            if self.use_mock:
                return {
                    'success': True,
                    'message': 'Mock AD connection successful',
                    'server': 'mock://ad.company.com',
                    'users_found': len(self.mock_users)
                }
            
            if self._connect_to_ad():
                # Test search
                test_users = self.search_users("*", 5)
                
                return {
                    'success': True,
                    'message': 'AD connection successful',
                    'server': self.config['server_url'],
                    'users_found': len(test_users)
                }
            else:
                return {
                    'success': False,
                    'message': 'AD connection failed',
                    'server': self.config['server_url'] if self.config else 'Unknown',
                    'users_found': 0
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'AD connection error: {str(e)}',
                'server': self.config['server_url'] if self.config else 'Unknown',
                'users_found': 0
            }
        finally:
            if self.connection:
                self.connection.unbind()
                self.connection = None
    
    def is_user_admin(self, user_info: Dict) -> bool:
        """
        Check if user should have admin privileges based on AD groups
        
        Args:
            user_info (Dict): User information from AD
            
        Returns:
            bool: True if user should be admin
        """
        if not user_info or 'memberOf' not in user_info:
            return False
        
        # Define admin groups (customize based on your AD setup)
        admin_groups = [
            'Domain Admins',
            'Administrators',
            'IT Admins',
            'NESOP Admins'
        ]
        
        user_groups = user_info.get('memberOf', [])
        
        for group in user_groups:
            for admin_group in admin_groups:
                if admin_group.lower() in group.lower():
                    return True
        
        return False
    
    def sync_ad_user_to_local(self, username: str, ad_user_info: Dict, balance: int = 0) -> bool:
        """
        Sync AD user to local database
        
        Args:
            username (str): Local username
            ad_user_info (Dict): AD user information
            balance (int): Initial balance for new users
            
        Returns:
            bool: True if sync successful
        """
        try:
            # Check if user already exists
            existing_user = db_utils.get_user(username)
            
            if existing_user:
                # Update existing user
                db_utils.update_ad_user_sync(
                    username=username,
                    ad_display_name=ad_user_info.get('displayName'),
                    ad_email=ad_user_info.get('mail')
                )
                logger.info(f"Updated existing AD user: {username}")
            else:
                # Create new AD user
                # Admin status is managed locally, not from AD groups
                is_admin = False
                
                db_utils.add_ad_user(
                    username=username,
                    ad_username=ad_user_info.get('sAMAccountName'),
                    ad_domain=self.config['domain'] if self.config else 'company.com',
                    ad_display_name=ad_user_info.get('displayName'),
                    ad_email=ad_user_info.get('mail'),
                    balance=balance,
                    is_admin=0  # Always create as regular user
                )
                logger.info(f"Created new AD user: {username} (admin permissions managed locally)")
            
            db_utils.log_ad_event(
                username=username,
                action='user_sync',
                details=f'Synced AD user to local database'
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error syncing AD user {username}: {str(e)}")
            db_utils.log_ad_event(
                username=username,
                action='user_sync_error',
                details=f'Error syncing user: {str(e)}',
                success=False,
                error_message=str(e)
            )
            return False
    
    def log_audit_event(self, username: str, action: str, details: str, metadata: dict = None) -> bool:
        """
        Log an audit event for user activities
        
        Args:
            username (str): Username performing the action
            action (str): Action performed (e.g., 'login_success', 'login_failed', 'user_import')
            details (str): Additional details about the action
            metadata (dict): Optional metadata about the action
            
        Returns:
            bool: True if logged successfully, False otherwise
        """
        try:
            success = action.endswith('_success') or action == 'user_import'
            return db_utils.log_ad_event(
                username=username,
                action=action,
                details=details,
                success=success
            )
        except Exception as e:
            logger.error(f"Error logging audit event: {str(e)}")
            return False

    @staticmethod
    def normalize_username(username: str, domain: str = None) -> str:
        """
        Normalize username to prevent duplicate users with different formats.
        
        This function extracts the base username from various formats:
        - username@domain.com -> username
        - domain\\username -> username
        - username -> username
        
        Args:
            username (str): Username in any format
            domain (str, optional): Domain to remove from username
            
        Returns:
            str: Normalized username (base username without domain)
        """
        if not username:
            return username
            
        normalized = username.strip()
        
        # Remove domain suffix if present (e.g., "username@company.com" -> "username")
        if '@' in normalized:
            normalized = normalized.split('@')[0]
        
        # Remove domain prefix if present (e.g., "COMPANY\\username" -> "username")
        if '\\' in normalized:
            normalized = normalized.split('\\')[-1]
        
        # If domain is provided, also try to remove it specifically
        if domain:
            # Remove @domain suffix
            if normalized.endswith(f"@{domain}"):
                normalized = normalized[:-len(f"@{domain}")]
            # Remove domain\ prefix
            if normalized.startswith(f"{domain}\\"):
                normalized = normalized[len(f"{domain}\\"):]
        
        return normalized.lower()  # Normalize to lowercase for consistency

# Global AD manager instance
ad_manager = ActiveDirectoryManager()

# Utility functions for easy access
def authenticate_user(username: str, password: str) -> Tuple[bool, Optional[Dict]]:
    """Authenticate user against AD"""
    return ad_manager.authenticate_user(username, password)

def search_users(search_term: str = "*", limit: int = 50) -> List[Dict]:
    """Search for users in AD"""
    return ad_manager.search_users(search_term, limit)

def test_ad_connection() -> Dict:
    """Test AD connection"""
    return ad_manager.test_connection()

def sync_ad_user_to_local(username: str, ad_user_info: Dict, balance: int = 0) -> bool:
    """Sync AD user to local database"""
    return ad_manager.sync_ad_user_to_local(username, ad_user_info, balance)

def set_mock_mode(use_mock: bool = True):
    """Enable or disable mock mode for testing"""
    global ad_manager
    ad_manager.use_mock = use_mock
    logger.info(f"AD Mock mode {'enabled' if use_mock else 'disabled'}")

def get_mock_users() -> Dict[str, Dict]:
    """Get mock users for testing"""
    return ad_manager.mock_users 