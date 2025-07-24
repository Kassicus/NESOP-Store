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
    """Manages email sending for order delivery and user notifications"""
    
    def __init__(self):
        self.email_config = config.get_email_config()
        self.ad_config = config.get_ad_config()
    
    def _generate_user_email(self, username: str) -> Optional[str]:
        """
        Generate user email address using username + AD_DOMAIN
        
        Args:
            username: The username to generate email for
            
        Returns:
            str: Generated email address (username@domain)
        """
        domain = self.ad_config.domain
        if domain and domain != "yourdomain.com":  # Don't use default placeholder
            return f"{username}@{domain}"
        else:
            logger.warning(f"AD_DOMAIN not properly configured, cannot generate email for user: {username}")
            return None

    def send_balance_change_notification(self, username: str, amount: float, new_balance: float, 
                                       transaction_type: str, note: str = "") -> bool:
        """
        Send email notification to user about balance changes
        
        Args:
            username: Username of the user
            amount: Amount added/deducted 
            new_balance: New balance after the change
            transaction_type: Type of transaction
            note: Additional note about the transaction
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        if not self.email_config.is_enabled:
            logger.info("Email is disabled, skipping balance change notification")
            return False
        
        user_email = self._generate_user_email(username)
        if not user_email:
            logger.warning(f"Cannot generate email address for user: {username}")
            return False
        
        try:
            # Create email content
            if amount > 0:
                subject = f"NESOP Store - Currency Added to Your Account"
                action_text = "added to"
            else:
                subject = f"NESOP Store - Currency Deducted from Your Account"
                action_text = "deducted from"
            
            body = self._create_balance_change_email_body(username, amount, new_balance, 
                                                        transaction_type, note, action_text)
            
            # Send email
            success = self._send_email(
                to_email=user_email,
                subject=subject,
                body=body,
                is_html=False
            )
            
            if success:
                logger.info(f"Balance change notification sent to {user_email} for user {username}")
            else:
                logger.error(f"Failed to send balance change notification to {user_email} for user {username}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending balance change notification to {username}: {str(e)}")
            return False

    def _create_balance_change_email_body(self, username: str, amount: float, new_balance: float,
                                        transaction_type: str, note: str, action_text: str) -> str:
        """Create the email body for balance change notification"""
        
        amount_abs = abs(amount)
        formatted_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        body = f"""Dear {username},

Your ESOP Store account balance has been updated.

TRANSACTION DETAILS:
===================
Amount {action_text} account: ₦ {amount_abs}
Transaction type: {transaction_type.replace('_', ' ').title()}
Your new balance: ₦ {new_balance}
Transaction date: {formatted_date}
"""
        
        if note:
            body += f"\nTransaction note: {note}\n"
        
        body += f"""
If you have any questions about this transaction, please reach out to the ESOP Committee.

Best regards,
ESOP Committee

---
This is an automated notification from ESOP Store.
"""
        
        return body

    def send_user_order_confirmation(self, username: str, order_details: Dict[str, Any]) -> bool:
        """
        Send order confirmation email directly to the user
        
        Args:
            username: Username of the customer
            order_details: Dictionary containing order information
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        if not self.email_config.is_enabled:
            logger.info("Email is disabled, skipping user order confirmation")
            return False
        
        user_email = self._generate_user_email(username)
        if not user_email:
            logger.warning(f"Cannot generate email address for user: {username}")
            return False
        
        try:
            # Create email content
            subject = f"Order Confirmation - NESOP Store Order #{order_details.get('order_id', 'N/A')}"
            body = self._create_user_order_confirmation_body(username, order_details)
            
            # Send email
            success = self._send_email(
                to_email=user_email,
                subject=subject,
                body=body,
                is_html=False
            )
            
            if success:
                logger.info(f"User order confirmation sent to {user_email} for user {username}")
            else:
                logger.error(f"Failed to send user order confirmation to {user_email} for user {username}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending user order confirmation to {username}: {str(e)}")
            return False

    def _create_user_order_confirmation_body(self, username: str, order_details: Dict[str, Any]) -> str:
        """Create the email body for user order confirmation"""
        
        order_id = order_details.get('order_id', 'N/A')
        order_date = order_details.get('order_date', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        items = order_details.get('items', [])
        total = order_details.get('total', 0)
        new_balance = order_details.get('customer_balance_after', 'N/A')
        
        # Create items list
        items_text = ""
        for item in items:
            items_text += f"- {item.get('name', 'N/A')} (₦ {item.get('price', 0)})\n"
        
        body = f"""Dear {username},

Thank you for your order from the ESOP Store!

ORDER DETAILS:
=============
Order ID: {order_id}
Order Date: {order_date}
Order Total: ₦ {total}

ITEMS ORDERED:
=============
{items_text}

ACCOUNT INFORMATION:
===================
Your new account balance: ₦ {new_balance}

Someone from the ESOP Committee will contact you shortly to arrange pickup or delivery of your items.

If you have any questions about your order, please reach out to the ESOP Committee.

Thank you for shopping with us!

Best regards,
ESOP Committee

---
This is an automated confirmation from the ESOP Store.
"""
        
        return body

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
            subject = f"New ESOP Store Order - {order_details.get('order_id', 'N/A')}"
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
        
        # Generate customer email for reference
        customer_email = self._generate_user_email(customer_username)
        
        body = f"""NEW ORDER - ESOP STORE
========================

A new order has been placed.

ORDER DETAILS:
=============
Order ID: {order_id}
Order Date: {order_date}
Order Total: ₦ {total}

CUSTOMER INFORMATION:
====================
Username: {customer_username}
Email: {customer_email if customer_email else 'Not available'}

Balance After Order: ₦ {customer_balance}

ITEMS TO FULFILL:
================
{items_text}

The customer has been automatically notified of their order confirmation.

---
Order processed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        return body

    def send_order_email(self, user_email: str, username: str, order_details: Dict[str, Any]) -> bool:
        """
        Send order confirmation email to user (DEPRECATED - use send_user_order_confirmation instead)
        
        Args:
            user_email: Recipient email address
            username: Username of the customer
            order_details: Dictionary containing order information
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        logger.warning("send_order_email is deprecated, use send_user_order_confirmation instead")
        return self.send_user_order_confirmation(username, order_details)
    
    def _create_order_email_body(self, username: str, order_details: Dict[str, Any]) -> str:
        """Create the email body for order confirmation (DEPRECATED)"""
        logger.warning("_create_order_email_body is deprecated, use _create_user_order_confirmation_body instead")
        return self._create_user_order_confirmation_body(username, order_details)
    
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

# New user notification functions
def send_balance_change_notification(username: str, amount: float, new_balance: float, 
                                   transaction_type: str, note: str = "") -> bool:
    """
    Send balance change notification email to user
    
    Args:
        username: Username of the user
        amount: Amount added/deducted 
        new_balance: New balance after the change
        transaction_type: Type of transaction
        note: Additional note about the transaction
        
    Returns:
        bool: True if sent successfully, False otherwise
    """
    return email_manager.send_balance_change_notification(username, amount, new_balance, 
                                                        transaction_type, note)

def send_user_order_confirmation(username: str, order_details: Dict[str, Any]) -> bool:
    """
    Send order confirmation email directly to the user
    
    Args:
        username: Username of the customer
        order_details: Dictionary containing order information
        
    Returns:
        bool: True if sent successfully, False otherwise
    """
    return email_manager.send_user_order_confirmation(username, order_details)

def generate_user_email(username: str) -> Optional[str]:
    """
    Generate user email address using username + AD_DOMAIN
    
    Args:
        username: The username to generate email for
        
    Returns:
        str: Generated email address (username@domain) or None if domain not configured
    """
    return email_manager._generate_user_email(username)

# Existing functions (maintained for backwards compatibility)
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
    Send order confirmation email (DEPRECATED - use send_user_order_confirmation instead)
    
    Args:
        user_email: Recipient email address
        username: Username of the customer
        order_details: Dictionary containing order information
        
    Returns:
        bool: True if sent successfully, False otherwise
    """
    logger.warning("send_order_confirmation is deprecated, use send_user_order_confirmation instead")
    return email_manager.send_user_order_confirmation(username, order_details)

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