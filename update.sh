#!/bin/bash
# ChoreChamp Update Script
# Pulls latest code, rebuilds container, and runs migrations

set -e  # Exit on any error

echo "========================================"
echo "  ChoreChamp Updater"
echo "========================================"
echo ""

cd "$(dirname "$0")"

# Check if we're in the right directory
if [ ! -f "docker-compose.yml" ]; then
    echo "Error: docker-compose.yml not found!"
    echo "Please run this script from the chorechamp directory."
    exit 1
fi

# Backup database before update
echo "[1/5] Backing up database..."
mkdir -p ~/backups
if [ -f "instance/chorechamp.db" ]; then
    cp instance/chorechamp.db ~/backups/chorechamp-$(date +%Y%m%d-%H%M%S).db
    echo "      Backup saved to ~/backups/"
else
    echo "      No existing database to backup"
fi

# Pull latest code
echo "[2/5] Pulling latest code from GitHub..."
git pull origin main

# Stop current container
echo "[3/5] Stopping current container..."
docker-compose down

# Rebuild with new code
echo "[4/5] Rebuilding container (this may take a few minutes)..."
docker-compose build

# Start the new container
echo "[5/5] Starting updated container..."
docker-compose up -d

# Wait for container to be ready
echo "      Waiting for container to start..."
sleep 5

# Run migrations
echo "      Running database migrations..."
docker exec chorechamp python /app/migrate.py

echo ""
echo "========================================"
echo "  Update complete!"
echo "========================================"
echo ""
echo "ChoreChamp is now running at: http://$(hostname):5001"
echo ""
echo "To view logs: docker-compose logs -f"
echo ""
