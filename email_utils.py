#!/usr/bin/env python3
"""
Email Utilities for NESOP Store
Handles email sending for order delivery via Exchange/SMTP.
"""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
from datetime import datetime
from typing import List, Optional, Dict, Any
import config

# Setup logging
logger = logging.getLogger(__name__)

class EmailManager:
    """Manages email sending for order delivery"""
    
    def __init__(self):
        self.email_config = config.get_email_config()
    
    def send_fulfillment_email(self, fulfillment_email: str, order_details: Dict[str, Any]) -> bool:
        """
        Send order notification email to fulfillment team
        
        Args:
            fulfillment_email: Email address of the fulfillment team
            order_details: Dictionary containing order information
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        if not self.email_config.is_enabled:
            logger.info("Email is disabled, skipping fulfillment notification")
            return False
        
        if not fulfillment_email:
            logger.warning("No fulfillment email address configured")
            return False
        
        try:
            # Create email content
            subject = f"New NESOP Store Order - {order_details.get('order_id', 'N/A')}"
            body = self._create_fulfillment_email_body(order_details)
            
            # Send email
            success = self._send_email(
                to_email=fulfillment_email,
                subject=subject,
                body=body,
                is_html=False
            )
            
            if success:
                logger.info(f"Order fulfillment notification sent to {fulfillment_email} for order {order_details.get('order_id', 'N/A')}")
            else:
                logger.error(f"Failed to send fulfillment notification to {fulfillment_email} for order {order_details.get('order_id', 'N/A')}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending fulfillment notification to {fulfillment_email}: {str(e)}")
            return False

    def _create_fulfillment_email_body(self, order_details: Dict[str, Any]) -> str:
        """Create the email body for fulfillment team notification"""
        
        order_id = order_details.get('order_id', 'N/A')
        order_date = order_details.get('order_date', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        customer_username = order_details.get('customer_username', 'Unknown')
        customer_display_name = order_details.get('customer_display_name', customer_username)
        items = order_details.get('items', [])
        total = order_details.get('total', 0)
        customer_balance = order_details.get('customer_balance_after', 'N/A')
        
        # Create items list
        items_text = ""
        for item in items:
            items_text += f"- {item.get('name', 'N/A')} (₦ {item.get('price', 0)})\n"
        
        body = f"""NEW ORDER - NESOP STORE
========================

A new order has been placed and requires fulfillment.

ORDER DETAILS:
=============
Order ID: {order_id}
Order Date: {order_date}
Order Total: ₦ {total}

CUSTOMER INFORMATION:
====================
Username: {customer_username}
Display Name: {customer_display_name}
Balance After Order: ₦ {customer_balance}

ITEMS TO FULFILL:
================
{items_text}

FULFILLMENT INSTRUCTIONS:
========================
1. Prepare the items listed above
2. Contact the customer to arrange pickup/delivery
3. Mark the order as fulfilled in the system

If you have any questions about this order, please contact the NESOP Store administrator.

---
This is an automated notification from NESOP Store.
Order processed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        return body

    def send_order_email(self, user_email: str, username: str, order_details: Dict[str, Any]) -> bool:
        """
        Send order confirmation email to user
        
        Args:
            user_email: Recipient email address
            username: Username of the customer
            order_details: Dictionary containing order information
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        if not self.email_config.is_enabled:
            logger.info("Email is disabled, skipping order email")
            return False
        
        if not user_email:
            logger.warning(f"No email address provided for user: {username}")
            return False
        
        try:
            # Create email content
            subject = f"Order Confirmation - NESOP Store Order #{order_details.get('order_id', 'N/A')}"
            body = self._create_order_email_body(username, order_details)
            
            # Send email
            success = self._send_email(
                to_email=user_email,
                subject=subject,
                body=body,
                is_html=False
            )
            
            if success:
                logger.info(f"Order confirmation email sent to {user_email} for user {username}")
            else:
                logger.error(f"Failed to send order confirmation email to {user_email} for user {username}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending order email to {user_email}: {str(e)}")
            return False
    
    def _create_order_email_body(self, username: str, order_details: Dict[str, Any]) -> str:
        """Create the email body for order confirmation"""
        
        order_id = order_details.get('order_id', 'N/A')
        order_date = order_details.get('order_date', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        items = order_details.get('items', [])
        total = order_details.get('total', 0)
        
                # Create items list
        items_text = ""
        for item in items:
            items_text += f"- {item.get('name', 'N/A')} (₦ {item.get('price', 0)})\n"

        body = f"""Dear {username},

Thank you for your order from NESOP Store!

Order Details:
==============
Order ID: {order_id}
Order Date: {order_date}

Items Ordered:
{items_text}
Total Amount: ₦ {total}

Your order has been successfully processed and your account balance has been updated.

If you have any questions about your order, please contact the NESOP Store administration.

Thank you for shopping with us!

Best regards,
NESOP Store Team
"""
        
        return body
    
    def _send_email(self, to_email: str, subject: str, body: str, is_html: bool = False) -> bool:
        """
        Send email via SMTP
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            body: Email body content
            is_html: Whether body is HTML content
            
        Returns:
            bool: True if sent successfully, False otherwise
        """
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = formataddr((self.email_config.from_name, self.email_config.from_address))
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Attach body
            mime_type = 'html' if is_html else 'plain'
            msg.attach(MIMEText(body, mime_type))
            
            # Connect to server and send
            with smtplib.SMTP(self.email_config.server, self.email_config.port, timeout=self.email_config.timeout) as server:
                if self.email_config.use_tls:
                    server.starttls()
                
                # Authenticate
                server.login(self.email_config.username, self.email_config.password)
                
                # Send email
                text = msg.as_string()
                server.sendmail(self.email_config.from_address, to_email, text)
                
                logger.info(f"Email sent successfully to {to_email}")
                return True
                
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP authentication failed: {str(e)}")
            return False
        except smtplib.SMTPConnectError as e:
            logger.error(f"Failed to connect to SMTP server: {str(e)}")
            return False
        except smtplib.SMTPRecipientsRefused as e:
            logger.error(f"Recipient email refused: {str(e)}")
            return False
        except smtplib.SMTPServerDisconnected as e:
            logger.error(f"SMTP server disconnected: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending email: {str(e)}")
            return False
    
    def test_connection(self) -> bool:
        """
        Test email server connection and authentication
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        if not self.email_config.is_enabled:
            logger.info("Email is disabled, skipping connection test")
            return False
        
        try:
            with smtplib.SMTP(self.email_config.server, self.email_config.port, timeout=self.email_config.timeout) as server:
                if self.email_config.use_tls:
                    server.starttls()
                
                # Test authentication
                server.login(self.email_config.username, self.email_config.password)
                
                logger.info("Email server connection test successful")
                return True
                
        except Exception as e:
            logger.error(f"Email server connection test failed: {str(e)}")
            return False
    
    def send_test_email(self, to_email: str) -> bool:
        """
        Send a test email to verify configuration
        
        Args:
            to_email: Email address to send test to
            
        Returns:
            bool: True if sent successfully, False otherwise
        """
        if not self.email_config.is_enabled:
            logger.info("Email is disabled, cannot send test email")
            return False
        
        subject = "NESOP Store Email Test"
        body = f"""This is a test email from NESOP Store.

If you received this email, the email configuration is working correctly.

Configuration Details:
- Server: {self.email_config.server}
- Port: {self.email_config.port}
- TLS: {self.email_config.use_tls}
- From: {self.email_config.from_address}

Test sent at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Best regards,
NESOP Store System
"""
        
        return self._send_email(to_email, subject, body)

# Global email manager instance
email_manager = EmailManager()

def send_order_notification(fulfillment_email: str, order_details: Dict[str, Any]) -> bool:
    """
    Send order notification email to fulfillment team
    
    Args:
        fulfillment_email: Email address of the fulfillment team
        order_details: Dictionary containing order information
        
    Returns:
        bool: True if sent successfully, False otherwise
    """
    return email_manager.send_fulfillment_email(fulfillment_email, order_details)

def send_order_confirmation(user_email: str, username: str, order_details: Dict[str, Any]) -> bool:
    """
    Send order confirmation email (DEPRECATED - use send_order_notification instead)
    
    Args:
        user_email: Recipient email address
        username: Username of the customer
        order_details: Dictionary containing order information
        
    Returns:
        bool: True if sent successfully, False otherwise
    """
    return email_manager.send_order_email(user_email, username, order_details)

def test_email_connection() -> bool:
    """
    Test email server connection
    
    Returns:
        bool: True if connection successful, False otherwise
    """
    return email_manager.test_connection()

def send_test_email(to_email: str) -> bool:
    """
    Send a test email
    
    Args:
        to_email: Email address to send test to
        
    Returns:
        bool: True if sent successfully, False otherwise
    """
    return email_manager.send_test_email(to_email) 