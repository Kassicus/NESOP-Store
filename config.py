#!/usr/bin/env python3
"""
Configuration Management for NESOP Store
Handles application configuration including AD integration settings.
"""

import os
import logging
from typing import Dict, Optional
from dataclasses import dataclass
from pathlib import Path

# Setup logging
logger = logging.getLogger(__name__)

@dataclass
class EmailConfig:
    """Email configuration for order delivery"""
    server: str = "your-exchange-server.yourdomain.com"
    port: int = 587
    username: str = "nesop-store@yourdomain.com"
    password: str = ""
    use_tls: bool = True
    from_address: str = "nesop-store@yourdomain.com"
    from_name: str = "NESOP Store"
    is_enabled: bool = False
    timeout: int = 30
    fulfillment_email: str = "nesop-fulfillment@yourdomain.com"

@dataclass
class ADConfig:
    """Active Directory configuration"""
    server_url: str = "ldap://your-dc.yourdomain.com"
    domain: str = "yourdomain.com"
    bind_dn: str = "CN=service_account,OU=Service Accounts,DC=yourdomain,DC=com"
    bind_password: str = ""
    user_base_dn: str = "OU=Users,DC=yourdomain,DC=com"
    user_filter: str = "(objectClass=user)"
    search_attributes: str = "sAMAccountName,displayName,mail,memberOf"
    use_ssl: bool = True
    port: int = 636
    timeout: int = 10
    is_enabled: bool = False
    # Simple bind mode settings
    simple_bind_mode: bool = False
    user_dn_pattern: str = "{username}@{domain}"
    admin_group: str = ""  # Optional: Leave empty to manage admin permissions locally

@dataclass
class AppConfig:
    """Application configuration"""
    # Flask settings
    debug: bool = False
    secret_key: str = "your-secret-key-change-this"
    
    # Database settings
    database_path: str = "nesop_store.db"
    
    # Upload settings
    upload_folder: str = "assets/images"
    max_file_size: int = 16 * 1024 * 1024  # 16MB
    allowed_extensions: set = None
    
    # AD settings
    ad_config: ADConfig = None
    
    # Email settings
    email_config: EmailConfig = None
    
    # Authentication settings
    local_admin_username: str = "fallback_admin"
    local_admin_password: str = "ChangeMe123!"
    
    # Mock mode for testing
    use_mock_ad: bool = False
    
    def __post_init__(self):
        if self.allowed_extensions is None:
            self.allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
        
        if self.ad_config is None:
            self.ad_config = ADConfig()
            
        if self.email_config is None:
            self.email_config = EmailConfig()

class ConfigManager:
    """Manages application configuration"""
    
    def __init__(self):
        self.config = AppConfig()
        self._load_from_env()
        self._validate_config()
    
    def _load_from_env(self):
        """Load configuration from environment variables"""
        try:
            # Flask settings
            self.config.debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
            self.config.secret_key = os.getenv('SECRET_KEY', self.config.secret_key)
            
            # Database settings
            self.config.database_path = os.getenv('DATABASE_PATH', self.config.database_path)
            
            # Upload settings
            self.config.upload_folder = os.getenv('UPLOAD_FOLDER', self.config.upload_folder)
            max_file_size = os.getenv('MAX_FILE_SIZE')
            if max_file_size:
                self.config.max_file_size = int(max_file_size)
            
            # AD settings
            self.config.ad_config.server_url = os.getenv('AD_SERVER_URL', self.config.ad_config.server_url)
            self.config.ad_config.domain = os.getenv('AD_DOMAIN', self.config.ad_config.domain)
            self.config.ad_config.bind_dn = os.getenv('AD_BIND_DN', self.config.ad_config.bind_dn)
            self.config.ad_config.bind_password = os.getenv('AD_BIND_PASSWORD', self.config.ad_config.bind_password)
            self.config.ad_config.user_base_dn = os.getenv('AD_USER_BASE_DN', self.config.ad_config.user_base_dn)
            self.config.ad_config.user_filter = os.getenv('AD_USER_FILTER', self.config.ad_config.user_filter)
            self.config.ad_config.search_attributes = os.getenv('AD_SEARCH_ATTRIBUTES', self.config.ad_config.search_attributes)
            self.config.ad_config.use_ssl = os.getenv('AD_USE_SSL', 'True').lower() == 'true'
            self.config.ad_config.simple_bind_mode = os.getenv('AD_SIMPLE_BIND_MODE', 'False').lower() == 'true'
            self.config.ad_config.user_dn_pattern = os.getenv('AD_USER_DN_PATTERN', self.config.ad_config.user_dn_pattern)
            self.config.ad_config.admin_group = os.getenv('AD_ADMIN_GROUP', self.config.ad_config.admin_group)
            
            ad_port = os.getenv('AD_PORT')
            if ad_port:
                self.config.ad_config.port = int(ad_port)
            
            ad_timeout = os.getenv('AD_TIMEOUT')
            if ad_timeout:
                self.config.ad_config.timeout = int(ad_timeout)
            
            self.config.ad_config.is_enabled = os.getenv('AD_ENABLED', 'False').lower() == 'true'
            
            # Email settings
            self.config.email_config.server = os.getenv('EMAIL_SERVER', self.config.email_config.server)
            self.config.email_config.username = os.getenv('EMAIL_USERNAME', self.config.email_config.username)
            self.config.email_config.password = os.getenv('EMAIL_PASSWORD', self.config.email_config.password)
            self.config.email_config.from_address = os.getenv('EMAIL_FROM_ADDRESS', self.config.email_config.from_address)
            self.config.email_config.from_name = os.getenv('EMAIL_FROM_NAME', self.config.email_config.from_name)
            self.config.email_config.use_tls = os.getenv('EMAIL_USE_TLS', 'True').lower() == 'true'
            self.config.email_config.is_enabled = os.getenv('EMAIL_ENABLED', 'False').lower() == 'true'
            self.config.email_config.fulfillment_email = os.getenv('EMAIL_FULFILLMENT_EMAIL', self.config.email_config.fulfillment_email)
            
            email_port = os.getenv('EMAIL_PORT')
            if email_port:
                self.config.email_config.port = int(email_port)
            
            email_timeout = os.getenv('EMAIL_TIMEOUT')
            if email_timeout:
                self.config.email_config.timeout = int(email_timeout)
            
            # Authentication settings
            self.config.local_admin_username = os.getenv('LOCAL_ADMIN_USERNAME', self.config.local_admin_username)
            self.config.local_admin_password = os.getenv('LOCAL_ADMIN_PASSWORD', self.config.local_admin_password)
            
            # Mock mode
            self.config.use_mock_ad = os.getenv('USE_MOCK_AD', 'False').lower() == 'true'
            
            logger.info("Configuration loaded from environment variables")
            
        except Exception as e:
            logger.error(f"Error loading configuration from environment: {str(e)}")
            logger.info("Using default configuration values")
    
    def _validate_config(self):
        """Validate configuration values"""
        try:
            # Validate paths
            if not os.path.exists(os.path.dirname(self.config.database_path)):
                os.makedirs(os.path.dirname(self.config.database_path), exist_ok=True)
            
            if not os.path.exists(self.config.upload_folder):
                os.makedirs(self.config.upload_folder, exist_ok=True)
            
            # Validate AD configuration if enabled
            if self.config.ad_config.is_enabled:
                if not self.config.ad_config.server_url or self.config.ad_config.server_url == "ldap://your-dc.yourdomain.com":
                    logger.warning("AD is enabled but server URL is not configured properly")
                
                if not self.config.ad_config.bind_password:
                    logger.warning("AD is enabled but bind password is not set")
            
            # Validate email configuration if enabled
            if self.config.email_config.is_enabled:
                if not self.config.email_config.server or self.config.email_config.server == "your-exchange-server.yourdomain.com":
                    logger.warning("Email is enabled but server is not configured properly")
                
                if not self.config.email_config.password:
                    logger.warning("Email is enabled but password is not set")
                
                if not self.config.email_config.from_address or self.config.email_config.from_address == "nesop-store@yourdomain.com":
                    logger.warning("Email is enabled but from_address is not configured properly")
            
            # Validate admin credentials
            if self.config.local_admin_password == "ChangeMe123!":
                logger.warning("Local admin password is still set to default. Please change it!")
            
            logger.info("Configuration validation completed")
            
        except Exception as e:
            logger.error(f"Configuration validation error: {str(e)}")
    
    def get_config(self) -> AppConfig:
        """Get the current configuration"""
        return self.config
    
    def get_ad_config(self) -> ADConfig:
        """Get the AD configuration"""
        return self.config.ad_config
    
    def get_email_config(self) -> EmailConfig:
        """Get the email configuration"""
        return self.config.email_config
    
    def update_ad_config(self, **kwargs):
        """Update AD configuration"""
        for key, value in kwargs.items():
            if hasattr(self.config.ad_config, key):
                setattr(self.config.ad_config, key, value)
                logger.info(f"Updated AD config: {key} = {value}")
            else:
                logger.warning(f"Unknown AD config key: {key}")
    
    def enable_ad(self, enabled: bool = True):
        """Enable or disable AD integration"""
        self.config.ad_config.is_enabled = enabled
        logger.info(f"AD integration {'enabled' if enabled else 'disabled'}")
    
    def enable_mock_mode(self, enabled: bool = True):
        """Enable or disable mock mode"""
        self.config.use_mock_ad = enabled
        logger.info(f"Mock AD mode {'enabled' if enabled else 'disabled'}")
    
    def get_database_path(self) -> str:
        """Get the database file path"""
        return os.path.abspath(self.config.database_path)
    
    def get_upload_folder(self) -> str:
        """Get the upload folder path"""
        return os.path.abspath(self.config.upload_folder)
    
    def is_file_allowed(self, filename: str) -> bool:
        """Check if file extension is allowed"""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in self.config.allowed_extensions
    
    def get_max_file_size(self) -> int:
        """Get maximum file size in bytes"""
        return self.config.max_file_size
    
    def create_env_template(self, filepath: str = ".env.template"):
        """Create a template environment file"""
        template = f"""# NESOP Store Configuration Template
# Copy this file to .env and update the values

# Flask Settings
FLASK_DEBUG=false
SECRET_KEY=your-secret-key-change-this

# Database Settings
DATABASE_PATH=nesop_store.db

# Upload Settings
UPLOAD_FOLDER=assets/images
MAX_FILE_SIZE=16777216

# Active Directory Settings
AD_SERVER_URL=ldap://your-dc.yourdomain.com
AD_DOMAIN=yourdomain.com
AD_BIND_DN=CN=service_account,OU=Service Accounts,DC=yourdomain,DC=com
AD_BIND_PASSWORD=your-service-account-password
AD_USER_BASE_DN=OU=Users,DC=yourdomain,DC=com
AD_USER_FILTER=(objectClass=user)
AD_SEARCH_ATTRIBUTES=sAMAccountName,displayName,mail,memberOf
AD_USE_SSL=true
AD_PORT=636
AD_TIMEOUT=10
AD_ENABLED=false

# Email Settings
EMAIL_SERVER=your-exchange-server.yourdomain.com
EMAIL_PORT=587
EMAIL_USERNAME=nesop-store@yourdomain.com
EMAIL_PASSWORD=your-email-password
EMAIL_FROM_ADDRESS=nesop-store@yourdomain.com
EMAIL_FROM_NAME=NESOP Store
EMAIL_USE_TLS=true
EMAIL_TIMEOUT=30
EMAIL_ENABLED=false
EMAIL_FULFILLMENT_EMAIL=nesop-fulfillment@yourdomain.com

# Authentication Settings
LOCAL_ADMIN_USERNAME=fallback_admin
LOCAL_ADMIN_PASSWORD=ChangeMe123!

# Testing Settings
USE_MOCK_AD=false
"""
        
        try:
            with open(filepath, 'w') as f:
                f.write(template)
            logger.info(f"Environment template created: {filepath}")
        except Exception as e:
            logger.error(f"Error creating environment template: {str(e)}")
    
    def load_env_file(self, filepath: str = ".env"):
        """Load environment variables from file"""
        try:
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            key, value = line.split('=', 1)
                            os.environ[key] = value
                
                # Reload configuration
                self._load_from_env()
                self._validate_config()
                logger.info(f"Loaded environment from: {filepath}")
            else:
                logger.warning(f"Environment file not found: {filepath}")
        except Exception as e:
            logger.error(f"Error loading environment file: {str(e)}")
    
    def get_summary(self) -> Dict:
        """Get a summary of the current configuration"""
        return {
            'app': {
                'debug': self.config.debug,
                'database_path': self.get_database_path(),
                'upload_folder': self.get_upload_folder(),
                'max_file_size': self.config.max_file_size,
                'allowed_extensions': list(self.config.allowed_extensions)
            },
            'ad': {
                'server_url': self.config.ad_config.server_url,
                'domain': self.config.ad_config.domain,
                'user_base_dn': self.config.ad_config.user_base_dn,
                'use_ssl': self.config.ad_config.use_ssl,
                'port': self.config.ad_config.port,
                'timeout': self.config.ad_config.timeout,
                'is_enabled': self.config.ad_config.is_enabled,
                'bind_password_set': bool(self.config.ad_config.bind_password)
            },
            'email': {
                'server': self.config.email_config.server,
                'port': self.config.email_config.port,
                'username': self.config.email_config.username,
                'from_address': self.config.email_config.from_address,
                'from_name': self.config.email_config.from_name,
                'use_tls': self.config.email_config.use_tls,
                'timeout': self.config.email_config.timeout,
                'is_enabled': self.config.email_config.is_enabled,
                'password_set': bool(self.config.email_config.password),
                'fulfillment_email': self.config.email_config.fulfillment_email
            },
            'auth': {
                'local_admin_username': self.config.local_admin_username,
                'local_admin_password_is_default': self.config.local_admin_password == "ChangeMe123!"
            },
            'testing': {
                'use_mock_ad': self.config.use_mock_ad
            }
        }

# Global configuration manager instance
config_manager = ConfigManager()

# Utility functions for easy access
def get_config() -> AppConfig:
    """Get the current configuration"""
    return config_manager.get_config()

def get_ad_config() -> ADConfig:
    """Get the AD configuration"""
    return config_manager.get_ad_config()

def get_email_config() -> EmailConfig:
    """Get the email configuration"""
    return config_manager.get_email_config()

def get_database_path() -> str:
    """Get the database file path"""
    return config_manager.get_database_path()

def get_upload_folder() -> str:
    """Get the upload folder path"""
    return config_manager.get_upload_folder()

def is_file_allowed(filename: str) -> bool:
    """Check if file extension is allowed"""
    return config_manager.is_file_allowed(filename)

def get_max_file_size() -> int:
    """Get maximum file size in bytes"""
    return config_manager.get_max_file_size()

def enable_ad(enabled: bool = True):
    """Enable or disable AD integration"""
    config_manager.enable_ad(enabled)

def enable_mock_mode(enabled: bool = True):
    """Enable or disable mock mode"""
    config_manager.enable_mock_mode(enabled)

def get_config_summary() -> Dict:
    """Get a summary of the current configuration"""
    return config_manager.get_summary()

def create_env_template(filepath: str = ".env.template"):
    """Create a template environment file"""
    config_manager.create_env_template(filepath)

def load_env_file(filepath: str = ".env"):
    """Load environment variables from file"""
    config_manager.load_env_file(filepath) 