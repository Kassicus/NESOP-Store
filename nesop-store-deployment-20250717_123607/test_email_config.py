#!/usr/bin/env python3
"""
Test Email Configuration for NESOP Store
Verify email settings and functionality before deployment.
"""

import logging
import sys
import os
from datetime import datetime

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
import email_utils

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_email_configuration():
    """Test email configuration and functionality"""
    print("NESOP Store Email Configuration Test")
    print("=" * 50)
    
    try:
        # Initialize configuration
        config_manager = config.ConfigManager()
        email_config = config_manager.get_email_config()
        
        # Display current configuration
        print("\n1. Current Email Configuration:")
        print("-" * 30)
        print(f"Enabled: {email_config.enabled}")
        print(f"Test Mode: {email_config.test_mode}")
        print(f"SMTP Server: {email_config.smtp_server}")
        print(f"SMTP Port: {email_config.smtp_port}")
        print(f"Use TLS: {email_config.use_tls}")
        print(f"Use SSL: {email_config.use_ssl}")
        print(f"Username: {email_config.username}")
        print(f"Password: {'*' * len(email_config.password) if email_config.password else '(not set)'}")
        print(f"From Email: {email_config.from_email}")
        print(f"From Name: {email_config.from_name}")
        print(f"To Email: {email_config.to_email}")
        print(f"To Name: {email_config.to_name}")
        print(f"Subject Prefix: {email_config.subject_prefix}")
        print(f"Timeout: {email_config.timeout}")
        
        if not email_config.enabled:
            print("\n❌ Email notifications are disabled!")
            print("Enable email notifications in configuration to test.")
            return False
        
        # Test 1: Email manager initialization
        print("\n2. Testing Email Manager Initialization:")
        print("-" * 30)
        try:
            email_manager = email_utils.EmailNotificationManager(config_manager)
            print("✅ Email manager initialized successfully")
        except Exception as e:
            print(f"❌ Failed to initialize email manager: {e}")
            return False
        
        # Test 2: Get email status
        print("\n3. Testing Email Status:")
        print("-" * 30)
        try:
            status = email_manager.get_email_status()
            print("✅ Email status retrieved successfully")
            print(f"   Authentication: {status['authentication']}")
            print(f"   Server: {status['smtp_server']}:{status['smtp_port']}")
        except Exception as e:
            print(f"❌ Failed to get email status: {e}")
            return False
        
        # Test 3: Connection test
        print("\n4. Testing SMTP Connection:")
        print("-" * 30)
        try:
            success, message = email_manager.test_email_connection()
            if success:
                print(f"✅ Connection test successful: {message}")
            else:
                print(f"❌ Connection test failed: {message}")
                return False
        except Exception as e:
            print(f"❌ Connection test error: {e}")
            return False
        
        # Test 4: Test mode verification
        if email_config.test_mode:
            print("\n5. Testing in Test Mode (No actual email sent):")
            print("-" * 30)
            
            # Create test order data
            test_order = {
                'username': 'test_user',
                'items': [
                    {'name': 'Test Product 1', 'price': 19.99},
                    {'name': 'Test Product 2', 'price': 29.99}
                ],
                'total': 49.98,
                'new_balance': 50.02,
                'order_date': datetime.now().strftime('%Y-%m-%d'),
                'order_time': datetime.now().strftime('%H:%M:%S')
            }
            
            try:
                success, message = email_manager.send_order_notification(test_order)
                if success:
                    print(f"✅ Test mode notification successful: {message}")
                    print("   (Check logs for test notification details)")
                else:
                    print(f"❌ Test mode notification failed: {message}")
                    return False
            except Exception as e:
                print(f"❌ Test mode notification error: {e}")
                return False
        
        # Test 5: Live email test (if not in test mode)
        else:
            print("\n5. Testing Live Email Sending:")
            print("-" * 30)
            
            response = input("Send a test email? This will send an actual email to your configured recipient. (y/N): ")
            if response.lower() in ['y', 'yes']:
                try:
                    success, message = email_manager.send_test_email()
                    if success:
                        print(f"✅ Test email sent successfully: {message}")
                        print(f"   Check {email_config.to_email} for the test email.")
                    else:
                        print(f"❌ Test email failed: {message}")
                        return False
                except Exception as e:
                    print(f"❌ Test email error: {e}")
                    return False
            else:
                print("⏭️  Live email test skipped")
        
        print("\n" + "=" * 50)
        print("✅ Email configuration test completed successfully!")
        print("=" * 50)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Email configuration test failed: {e}")
        logger.error(f"Email configuration test failed: {e}")
        return False

def main():
    """Main test function"""
    print("Starting email configuration test...")
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    success = test_email_configuration()
    
    if success:
        print("\n🎉 All tests passed! Email configuration is working correctly.")
        print("\nNext steps:")
        print("1. Configure your email settings in deploy_config.py")
        print("2. Test with actual Exchange server settings")
        print("3. Deploy and verify email notifications work in production")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed. Please check your email configuration.")
        print("\nTroubleshooting:")
        print("1. Verify SMTP server address and port")
        print("2. Check username/password if using authentication")
        print("3. Verify firewall/network connectivity")
        print("4. Test with anonymous relay if available")
        sys.exit(1)

if __name__ == "__main__":
    main() 