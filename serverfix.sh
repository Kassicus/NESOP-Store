# Change ownership of all files to www-data
sudo chown -R www-data:www-data /var/www/thesuchows/nesop

# Set proper permissions for directories
sudo find /var/www/thesuchows/nesop -type d -exec chmod 755 {} \;

# Set proper permissions for files
sudo find /var/www/thesuchows/nesop -type f -exec chmod 644 {} \;

# Special permissions for specific files/directories
# Make the database file writable
sudo chmod 664 /var/www/thesuchows/nesop/nesop_store.db

# Make the assets/images directory writable
sudo chmod 775 /var/www/thesuchows/nesop/assets/images

# Make sure Python files are executable
sudo chmod 755 /var/www/thesuchows/nesop/server.py
sudo chmod 755 /var/www/thesuchows/nesop/wsgi.py
sudo chmod 755 /var/www/thesuchows/nesop/db_utils.py