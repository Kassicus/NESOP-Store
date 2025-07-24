# NESOP Store v1.1.0 - Inventory Tracking Update

## 🚀 Update Overview

This update package adds comprehensive **inventory tracking** functionality to your NESOP Store deployment. 

### ✨ New Features

- **Real-time inventory tracking** with automatic decrement on purchase
- **Enhanced admin inventory management** with quantity controls
- **Storefront inventory display** showing available quantities
- **Smart inventory validation** preventing overselling
- **Low stock warnings** for items with limited availability
- **Detailed error messages** for insufficient inventory scenarios

## 📦 Update Package Details

**Package:** `nesop-store-update-v1.1.0-20250724_100533.tar.gz`  
**Version:** 1.1.0  
**Type:** Feature Update (Database Migration Required)  
**Size:** 11.76 MB  

### Files Updated
- `server.py` - Inventory checking and decrement logic
- `db_utils.py` - New inventory management functions  
- `admin-inventory.html` - Enhanced quantity management UI
- `cart.html` - Inventory error handling
- `scripts/store.js` - Storefront inventory display
- `styles/main.css` - Inventory styling
- All other standard application files

### Database Migration
- `migrate_quantity_tracking.py` - Adds `quantity` column to items table

**Note:** This version removes the problematic `migrate_username_normalization.py` that caused deployment failures on some servers.

**JavaScript Fix:** Added proper HTTP error handling to prevent JSON parsing errors when API endpoints return error pages.

**Backward Compatibility Fix:** Added graceful fallback for databases that haven't run the quantity migration yet, preventing HTTP 500 errors during deployment.

## 🔧 Pre-Update Requirements

1. **Backup your system** (automatically handled by update manager)
2. **Verify system health**:
   ```bash
   sudo python3 /opt/nesop-store/validate_deployment.py
   ```
3. **Check disk space** (at least 50MB free):
   ```bash
   df -h /opt/nesop-store
   ```

## 📋 Installation Instructions

### Step 1: Transfer Update Package

Copy the update package to your server:

```bash
# Via SCP
scp nesop-store-update-v1.1.0-20250724_100533.tar.gz user@your-server:/tmp/

# Or via other file transfer method
```

### Step 2: Extract Update Package

On your server:

```bash
ssh user@your-server
cd /tmp
tar -xzf nesop-store-update-v1.1.0-20250724_100533.tar.gz
```

### Step 3: Apply Update

Run the update manager as root:

```bash
cd /tmp/nesop-store-update-v1.1.0-20250724_100533
sudo python3 /opt/nesop-store/update_manager.py apply .
```

### Step 4: Validate Update

Verify the update was successful:

```bash
sudo python3 /opt/nesop-store/validate_deployment.py
```

## ✅ Post-Update Verification

After applying the update, verify these features work:

### 1. Database Migration
Check that the quantity column was added:
```bash
sqlite3 /opt/nesop-store/nesop_store.db "PRAGMA table_info(items);"
```
You should see a `quantity` column in the output.

### 2. Admin Panel
- Log into the admin panel
- Navigate to **Inventory Management**  
- Verify you can see and edit product quantities
- Check that the "Total Inventory" statistic appears

### 3. Storefront Display
- Visit the main store page
- Verify products show inventory badges:
  - "X available" for items with >5 in stock
  - "Only X left" (orange) for items with ≤5 in stock
  - "Out of Stock" (red) for items with 0 quantity

### 4. Purchase Flow
- Add items to cart
- Attempt checkout
- Verify inventory decrements correctly after purchase
- Test insufficient inventory error handling

## 🎯 New Admin Features

### Inventory Management Page
Access via: Admin Dashboard → Inventory Management

**New Features:**
- **Quantity Column** in product table
- **Total Inventory** statistic card
- **Quantity Input Field** in add/edit product modals
- **Real-time inventory display** with color-coded status

### Setting Initial Inventory
1. Go to **Admin Dashboard** → **Inventory Management**
2. Click **Edit** on any product
3. Set the **Quantity** field to your current stock level
4. Click **Save Changes**

## 🛡️ System Behavior Changes

### Purchase Processing
- **Before purchase**: System validates inventory availability
- **Insufficient inventory**: Order blocked with detailed error message
- **Successful purchase**: Inventory automatically decremented by 1
- **Zero inventory**: Product automatically shown as "Out of Stock"

### Error Handling
- **Detailed inventory errors** show exactly which items are insufficient
- **Graceful degradation** if inventory update fails (payment still processes)
- **Comprehensive logging** of all inventory changes

## 🔄 Rollback Instructions

If you encounter issues, you can rollback:

```bash
# List available backups
sudo python3 /opt/nesop-store/update_manager.py list-backups

# Rollback to previous version
sudo python3 /opt/nesop-store/update_manager.py rollback pre_update_20250724_100533
```

## 🆘 Troubleshooting

### Update Failed
```bash
# Check update logs
sudo tail -f /opt/nesop-store/logs/update.log

# Check service status
sudo systemctl status nesop-store

# Manual service restart
sudo systemctl restart nesop-store
```

### Database Issues
```bash
# Run migration manually
cd /opt/nesop-store
sudo python3 migrate_quantity_tracking.py

# Check database connectivity
sudo python3 validate_deployment.py --check database
```

### Permission Issues
```bash
# Fix file permissions
sudo chown -R nesop:nesop /opt/nesop-store/
sudo chmod +x /opt/nesop-store/*.py
```

## 📊 Update Statistics

- **Files Updated:** 10 core application files
- **Directories Updated:** 3 (scripts, styles, assets)
- **Database Migrations:** 1 (quantity column addition)
- **New Features:** 6 major inventory tracking features
- **Backward Compatible:** Yes (with automatic migration)

## 🎉 What's Next

After this update, you'll have complete inventory tracking capability:

1. **Set initial inventory** for all your products
2. **Monitor inventory levels** through the admin dashboard  
3. **Automatic inventory management** as customers make purchases
4. **Low stock alerts** to help with reordering

---

## 🔗 Support

For questions or issues with this update:
1. Check the logs in `/opt/nesop-store/logs/`
2. Run validation: `sudo python3 validate_deployment.py`
3. Review this guide for troubleshooting steps
4. Use rollback if necessary

**Enjoy your new inventory tracking system!** 🛍️ 