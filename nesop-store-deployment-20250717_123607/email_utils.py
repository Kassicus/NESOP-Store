#!/usr/bin/env python3
"""
Email Notification Utilities for NESOP Store
Provides email notification functionality using smtplib for Exchange server integration.
"""

import smtplib
import ssl
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import config

# Setup logging
logger = logging.getLogger(__name__)

class EmailNotificationManager:
    """Handles email notifications for order processing"""
    
    def __init__(self, config_manager: config.ConfigManager = None):
        """Initialize email notification manager"""
        self.config_manager = config_manager or config.ConfigManager()
        self.email_config = self.config_manager.get_email_config()
        
    def _create_smtp_connection(self) -> Tuple[bool, Optional[smtplib.SMTP], str]:
        """Create SMTP connection to email server"""
        try:
            smtp_server = None
            
            # Create SMTP connection based on SSL/TLS settings
            if self.email_config.use_ssl:
                # Use SSL connection (typically port 465)
                context = ssl.create_default_context()
                smtp_server = smtplib.SMTP_SSL(
                    self.email_config.smtp_server,
                    self.email_config.smtp_port,
                    context=context,
                    timeout=self.email_config.timeout
                )
                logger.info(f"Connected to SMTP server via SSL: {self.email_config.smtp_server}:{self.email_config.smtp_port}")
            else:
                # Use regular SMTP connection
                smtp_server = smtplib.SMTP(
                    self.email_config.smtp_server,
                    self.email_config.smtp_port,
                    timeout=self.email_config.timeout
                )
                logger.info(f"Connected to SMTP server: {self.email_config.smtp_server}:{self.email_config.smtp_port}")
                
                # Enable STARTTLS if configured
                if self.email_config.use_tls:
                    context = ssl.create_default_context()
                    smtp_server.starttls(context=context)
                    logger.info("STARTTLS enabled")
            
            # Authenticate if username/password provided
            if self.email_config.username and self.email_config.password:
                smtp_server.login(self.email_config.username, self.email_config.password)
                logger.info(f"Authenticated with username: {self.email_config.username}")
            else:
                logger.info("Using anonymous relay (no authentication)")
            
            return True, smtp_server, "Connected successfully"
            
        except smtplib.SMTPAuthenticationError as e:
            error_msg = f"SMTP authentication failed: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg
        except smtplib.SMTPConnectError as e:
            error_msg = f"SMTP connection failed: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg
        except smtplib.SMTPException as e:
            error_msg = f"SMTP error: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg
        except Exception as e:
            error_msg = f"Unexpected error connecting to SMTP server: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg
    
    def _create_order_email(self, order_data: Dict) -> MIMEMultipart:
        """Create email message for order notification"""
        
        # Create multipart message
        message = MIMEMultipart("alternative")
        
        # Email headers
        message["From"] = f"{self.email_config.from_name} <{self.email_config.from_email}>"
        message["To"] = f"{self.email_config.to_name} <{self.email_config.to_email}>"
        message["Subject"] = Header(
            f"{self.email_config.subject_prefix} New Order from {order_data['username']}",
            "utf-8"
        )
        
        # Create email body
        order_text = self._format_order_text(order_data)
        order_html = self._format_order_html(order_data)
        
        # Attach text and HTML versions
        message.attach(MIMEText(order_text, "plain", "utf-8"))
        message.attach(MIMEText(order_html, "html", "utf-8"))
        
        return message
    
    def _format_order_text(self, order_data: Dict) -> str:
        """Format order data as plain text"""
        lines = [
            f"New Order Received",
            f"=" * 50,
            f"",
            f"Customer: {order_data['username']}",
            f"Order Date: {order_data['order_date']}",
            f"Order Time: {order_data['order_time']}",
            f"",
            f"Items Ordered:",
            f"-" * 20,
        ]
        
        for item in order_data['items']:
            lines.append(f"• {item['name']} - €{item['price']:.2f}")
        
        lines.extend([
            f"",
            f"Total Amount: €{order_data['total']:.2f}",
            f"",
            f"Customer Balance After Purchase: €{order_data['new_balance']:.2f}",
            f"",
            f"=" * 50,
            f"This is an automated notification from NESOP Store",
            f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        ])
        
        return "\n".join(lines)
    
    def _format_order_html(self, order_data: Dict) -> str:
        """Format order data as HTML"""
        items_html = ""
        for item in order_data['items']:
            items_html += f"""
            <tr>
                <td style="padding: 8px; border-bottom: 1px solid #eee;">{item['name']}</td>
                <td style="padding: 8px; border-bottom: 1px solid #eee; text-align: right;">€{item['price']:.2f}</td>
            </tr>
            """
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>New Order Notification</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                }}
                .header {{
                    background-color: #1976d2;
                    color: white;
                    padding: 20px;
                    text-align: center;
                }}
                .content {{
                    padding: 20px;
                }}
                .order-info {{
                    background-color: #f9f9f9;
                    padding: 15px;
                    border-radius: 5px;
                    margin-bottom: 20px;
                }}
                .items-table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin-bottom: 20px;
                }}
                .items-table th {{
                    background-color: #1976d2;
                    color: white;
                    padding: 10px;
                    text-align: left;
                }}
                .total {{
                    font-size: 18px;
                    font-weight: bold;
                    color: #1976d2;
                    text-align: right;
                    margin-top: 20px;
                }}
                .footer {{
                    background-color: #f9f9f9;
                    padding: 10px;
                    text-align: center;
                    font-size: 12px;
                    color: #666;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🛍️ New Order Received</h1>
            </div>
            
            <div class="content">
                <div class="order-info">
                    <h2>Order Details</h2>
                    <p><strong>Customer:</strong> {order_data['username']}</p>
                    <p><strong>Order Date:</strong> {order_data['order_date']}</p>
                    <p><strong>Order Time:</strong> {order_data['order_time']}</p>
                </div>
                
                <h3>Items Ordered</h3>
                <table class="items-table">
                    <thead>
                        <tr>
                            <th>Item</th>
                            <th>Price</th>
                        </tr>
                    </thead>
                    <tbody>
                        {items_html}
                    </tbody>
                </table>
                
                <div class="total">
                    Total Amount: €{order_data['total']:.2f}
                </div>
                
                <div class="order-info">
                    <p><strong>Customer Balance After Purchase:</strong> €{order_data['new_balance']:.2f}</p>
                </div>
            </div>
            
            <div class="footer">
                <p>This is an automated notification from NESOP Store</p>
                <p>Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def send_order_notification(self, order_data: Dict) -> Tuple[bool, str]:
        """
        Send order notification email
        
        Args:
            order_data: Dictionary containing order information
                - username: Customer username
                - items: List of items with name and price
                - total: Total order amount
                - new_balance: Customer balance after purchase
                - order_date: Order date string
                - order_time: Order time string
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        
        if not self.email_config.enabled:
            logger.info("Email notifications are disabled")
            return False, "Email notifications are disabled"
        
        if self.email_config.test_mode:
            logger.info("Email test mode enabled - logging order instead of sending email")
            order_text = self._format_order_text(order_data)
            logger.info(f"ORDER NOTIFICATION (TEST MODE):\n{order_text}")
            return True, "Order notification logged (test mode)"
        
        try:
            # Create SMTP connection
            success, smtp_server, error_msg = self._create_smtp_connection()
            if not success:
                return False, error_msg
            
            # Create email message
            message = self._create_order_email(order_data)
            
            # Send email
            smtp_server.send_message(message)
            smtp_server.quit()
            
            logger.info(f"Order notification email sent successfully to {self.email_config.to_email}")
            return True, "Order notification email sent successfully"
            
        except Exception as e:
            error_msg = f"Failed to send order notification email: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def test_email_connection(self) -> Tuple[bool, str]:
        """
        Test email server connection and authentication
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        
        if not self.email_config.enabled:
            return False, "Email notifications are disabled"
        
        try:
            # Test connection
            success, smtp_server, error_msg = self._create_smtp_connection()
            if not success:
                return False, error_msg
            
            # Close connection
            smtp_server.quit()
            
            logger.info("Email connection test successful")
            return True, "Email connection test successful"
            
        except Exception as e:
            error_msg = f"Email connection test failed: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def send_test_email(self) -> Tuple[bool, str]:
        """
        Send a test email to verify email configuration
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        
        if not self.email_config.enabled:
            return False, "Email notifications are disabled"
        
        # Create test order data
        test_order_data = {
            'username': 'test_user',
            'items': [
                {'name': 'Test Item 1', 'price': 10.00},
                {'name': 'Test Item 2', 'price': 15.50}
            ],
            'total': 25.50,
            'new_balance': 74.50,
            'order_date': datetime.now().strftime('%Y-%m-%d'),
            'order_time': datetime.now().strftime('%H:%M:%S')
        }
        
        try:
            # Create SMTP connection
            success, smtp_server, error_msg = self._create_smtp_connection()
            if not success:
                return False, error_msg
            
            # Create test email message
            message = MIMEMultipart()
            message["From"] = f"{self.email_config.from_name} <{self.email_config.from_email}>"
            message["To"] = f"{self.email_config.to_name} <{self.email_config.to_email}>"
            message["Subject"] = Header(
                f"{self.email_config.subject_prefix} Test Email - Email Configuration Working",
                "utf-8"
            )
            
            # Create test email body
            test_text = f"""
NESOP Store Email Test
======================

This is a test email to verify that your email configuration is working correctly.

Configuration Details:
- SMTP Server: {self.email_config.smtp_server}:{self.email_config.smtp_port}
- Use TLS: {self.email_config.use_tls}
- Use SSL: {self.email_config.use_ssl}
- Authentication: {'Yes' if self.email_config.username else 'Anonymous relay'}
- From: {self.email_config.from_email}
- To: {self.email_config.to_email}

If you received this email, your email configuration is working correctly!

Test performed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """
            
            message.attach(MIMEText(test_text, "plain", "utf-8"))
            
            # Send test email
            smtp_server.send_message(message)
            smtp_server.quit()
            
            logger.info(f"Test email sent successfully to {self.email_config.to_email}")
            return True, "Test email sent successfully"
            
        except Exception as e:
            error_msg = f"Failed to send test email: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def get_email_status(self) -> Dict:
        """
        Get current email configuration status
        
        Returns:
            Dictionary with email configuration status
        """
        return {
            'enabled': self.email_config.enabled,
            'test_mode': self.email_config.test_mode,
            'smtp_server': self.email_config.smtp_server,
            'smtp_port': self.email_config.smtp_port,
            'use_tls': self.email_config.use_tls,
            'use_ssl': self.email_config.use_ssl,
            'from_email': self.email_config.from_email,
            'to_email': self.email_config.to_email,
            'authentication': 'Yes' if self.email_config.username else 'Anonymous relay',
            'subject_prefix': self.email_config.subject_prefix
        }

# Global instance for easy access
email_manager = EmailNotificationManager()

def send_order_notification(order_data: Dict) -> Tuple[bool, str]:
    """
    Convenience function to send order notification email
    
    Args:
        order_data: Dictionary containing order information
    
    Returns:
        Tuple of (success: bool, message: str)
    """
    return email_manager.send_order_notification(order_data)

def test_email_connection() -> Tuple[bool, str]:
    """
    Convenience function to test email connection
    
    Returns:
        Tuple of (success: bool, message: str)
    """
    return email_manager.test_email_connection()

def send_test_email() -> Tuple[bool, str]:
    """
    Convenience function to send test email
    
    Returns:
        Tuple of (success: bool, message: str)
    """
    return email_manager.send_test_email() 