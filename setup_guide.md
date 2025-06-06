# Ubuntu Server Setup Guide

This guide will help you set up the development environment for the NESOP Store project on an Ubuntu server.

## 1. System Update
First, ensure your system is up to date:
```bash
sudo apt update
sudo apt upgrade -y
```

## 2. Install Apache2
```bash
sudo apt install apache2 -y
sudo systemctl enable apache2
sudo systemctl start apache2
```

Verify Apache2 is running:
```bash
sudo systemctl status apache2
```

## 3. Install MariaDB
```bash
sudo apt install mariadb-server -y
sudo systemctl enable mariadb
sudo systemctl start mariadb
```

Secure your MariaDB installation:
```bash
sudo mysql_secure_installation
```
During this process:
- Set a root password
- Remove anonymous users
- Disallow root login remotely
- Remove test database
- Reload privilege tables

## 4. Install PHP and Required Extensions
```bash
sudo apt install php php-mysql php-curl php-gd php-mbstring php-xml php-zip php-intl php-json php-common php-cli -y
```

## 5. Configure Apache2
Enable required Apache modules:
```bash
sudo a2enmod rewrite
sudo a2enmod headers
sudo systemctl restart apache2
```

## 6. Configure PHP
Edit PHP configuration:
```bash
sudo nano /etc/php/7.4/apache2/php.ini
```

Make these recommended changes:
```ini
memory_limit = 256M
upload_max_filesize = 64M
post_max_size = 64M
max_execution_time = 300
date.timezone = UTC
```

## 7. Create Project Directory
```bash
sudo mkdir -p /var/www/nesop-store
sudo chown -R $USER:$USER /var/www/nesop-store
```

## 8. Configure Virtual Host
Create a new virtual host configuration:
```bash
sudo nano /etc/apache2/sites-available/nesop-store.conf
```

Add the following configuration:
```apache
<VirtualHost *:80>
    ServerName nesop-store.local
    ServerAdmin webmaster@localhost
    DocumentRoot /var/www/nesop-store/public

    <Directory /var/www/nesop-store/public>
        Options Indexes FollowSymLinks
        AllowOverride All
        Require all granted
    </Directory>

    ErrorLog ${APACHE_LOG_DIR}/nesop-store-error.log
    CustomLog ${APACHE_LOG_DIR}/nesop-store-access.log combined
</VirtualHost>
```

Enable the site and restart Apache:
```bash
sudo a2ensite nesop-store.conf
sudo systemctl restart apache2
```

## 9. Set Up Database
Log into MariaDB:
```bash
sudo mysql -u root -p
```

Create database and user:
```sql
CREATE DATABASE nesop_store;
CREATE USER 'nesop_user'@'localhost' IDENTIFIED BY 'your_secure_password';
GRANT ALL PRIVILEGES ON nesop_store.* TO 'nesop_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

## 10. Clone Repository
```bash
cd /var/www/nesop-store
git clone [your-repository-url] .
```

## 11. Set Permissions
```bash
sudo chown -R www-data:www-data /var/www/nesop-store
sudo chmod -R 755 /var/www/nesop-store
```

## 12. Test Installation
Create a test PHP file:
```bash
echo "<?php phpinfo(); ?>" | sudo tee /var/www/nesop-store/public/info.php
```

Visit `http://your-server-ip/info.php` to verify PHP is working.

## 13. Security Considerations
After confirming everything works:
1. Remove the info.php file:
```bash
sudo rm /var/www/nesop-store/public/info.php
```

2. Configure firewall:
```bash
sudo ufw allow 'Apache Full'
sudo ufw enable
```

## 14. Next Steps
1. Update your project's configuration files with the database credentials
2. Import the initial database schema
3. Configure email settings
4. Begin development

## Troubleshooting
- Check Apache error logs: `sudo tail -f /var/log/apache2/error.log`
- Check MariaDB logs: `sudo tail -f /var/log/mysql/error.log`
- Verify PHP installation: `php -v`
- Check Apache status: `sudo systemctl status apache2`
- Check MariaDB status: `sudo systemctl status mariadb`

## Notes
- Replace `your_secure_password` with a strong password
- Replace `[your-repository-url]` with your actual Git repository URL
- Adjust PHP version numbers if you're using a different version
- Consider setting up SSL/TLS for production use 