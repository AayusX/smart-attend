#!/bin/bash

# Smart Attendance System - Backup Script

set -e

BACKUP_DIR="./backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="smart_attendance_$TIMESTAMP"

echo "=== Smart Attendance System Backup ==="

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup database
echo "Backing up database..."
if [ -f "./data/attendance.db" ]; then
    cp ./data/attendance.db "$BACKUP_DIR/$BACKUP_NAME.db"
    echo "Database backed up to $BACKUP_DIR/$BACKUP_NAME.db"
fi

# Backup configuration
echo "Backing up configuration..."
tar -czf "$BACKUP_DIR/$BACKUP_NAME_config.tar.gz" .env docker-compose.yml nginx/ 2>/dev/null || true

# Backup face templates (if stored separately)
if [ -d "./data/templates" ]; then
    echo "Backing up face templates..."
    tar -czf "$BACKUP_DIR/$BACKUP_NAME_templates.tar.gz" ./data/templates/
fi

# Clean old backups (keep last 7 days)
echo "Cleaning old backups..."
find $BACKUP_DIR -name "smart_attendance_*" -mtime +7 -delete 2>/dev/null || true

echo ""
echo "=== Backup Complete ==="
echo "Backup location: $BACKUP_DIR/$BACKUP_NAME*"
echo ""

# List current backups
echo "Current backups:"
ls -lh $BACKUP_DIR/smart_attendance_* 2>/dev/null || echo "No backups found"
