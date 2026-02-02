# ChoreChamp Docker Deployment Guide

This guide covers deploying ChoreChamp on a Raspberry Pi or any Linux server using Docker.

## Prerequisites

- Raspberry Pi 3/4/5 or Linux server
- Docker and Docker Compose installed
- Git (to clone the repository)

### Installing Docker on Raspberry Pi

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add your user to docker group (avoids needing sudo)
sudo usermod -aG docker $USER

# Install Docker Compose
sudo apt install docker-compose -y

# Log out and back in for group changes to take effect
```

## Deployment Steps

### 1. Clone the Repository

```bash
cd ~
git clone <your-repo-url> chorechamp
cd chorechamp
```

### 2. Create Environment File

Create a `.env` file with your configuration:

```bash
cat > .env << 'EOF'
# Required: Generate a secure secret key
SECRET_KEY=your-very-long-random-secret-key-here

# Optional: For encrypted email passwords in database
SETTINGS_ENCRYPTION_KEY=

# Email configuration (can also be set via Admin UI)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your.email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=ChoreChamp <your.email@gmail.com>
EOF
```

Generate a secure secret key:
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### 3. Build and Start

```bash
# Build the Docker image
docker-compose build

# Start the container
docker-compose up -d

# Check logs
docker-compose logs -f
```

### 4. Verify Deployment

```bash
# Check container is running
docker ps

# Test the application
curl http://localhost:5001
```

Access the app at `http://<your-pi-ip>:5001`

## First-Time Setup

1. Navigate to `http://<your-pi-ip>:5001`
2. Create your first admin user (first user created becomes admin)
3. Configure email settings via Admin > Email Settings
4. Add children and chores

## Database Location

The SQLite database is stored in `./instance/chorechamp.db` and persisted via Docker volume.

## Updating

```bash
cd ~/chorechamp

# Pull latest changes
git pull

# Rebuild and restart
docker-compose down
docker-compose build
docker-compose up -d
```

## Backup

### Manual Backup

```bash
# Stop the container first for consistency
docker-compose down

# Copy database
cp instance/chorechamp.db ~/backups/chorechamp-$(date +%Y%m%d).db

# Restart
docker-compose up -d
```

### Automated Backup Script

Create `~/backup-chorechamp.sh`:

```bash
#!/bin/bash
BACKUP_DIR=~/backups/chorechamp
mkdir -p $BACKUP_DIR

# Create backup
cp ~/chorechamp/instance/chorechamp.db $BACKUP_DIR/chorechamp-$(date +%Y%m%d-%H%M).db

# Keep only last 7 days
find $BACKUP_DIR -name "*.db" -mtime +7 -delete
```

Add to crontab:
```bash
crontab -e
# Add: 0 2 * * * /home/pi/backup-chorechamp.sh
```

## Reverse Proxy (Optional)

For HTTPS access, use a reverse proxy like Caddy or nginx.

### Using Caddy (Recommended)

Install Caddy:
```bash
sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
sudo apt update
sudo apt install caddy
```

Configure `/etc/caddy/Caddyfile`:
```
chorechamp.yourdomain.com {
    reverse_proxy localhost:5001
}
```

Start Caddy:
```bash
sudo systemctl enable caddy
sudo systemctl start caddy
```

### Using nginx

```bash
sudo apt install nginx -y
```

Create `/etc/nginx/sites-available/chorechamp`:
```nginx
server {
    listen 80;
    server_name chorechamp.local;

    location / {
        proxy_pass http://localhost:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable and start:
```bash
sudo ln -s /etc/nginx/sites-available/chorechamp /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## Troubleshooting

### Container won't start

```bash
# Check logs
docker-compose logs

# Common issues:
# - Port 5001 already in use: change port in docker-compose.yml
# - Permission issues: ensure instance/ directory exists
```

### Database errors

```bash
# Reset database (WARNING: deletes all data)
docker-compose down
rm -f instance/chorechamp.db
docker-compose up -d
```

### Memory issues on Raspberry Pi

If running low on memory, reduce workers in Dockerfile:
```dockerfile
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "1", "run:app"]
```

### View container logs

```bash
# All logs
docker-compose logs

# Follow logs
docker-compose logs -f

# Last 100 lines
docker-compose logs --tail=100
```

## Performance Tips

1. **Use a USB SSD** instead of SD card for better database performance
2. **Enable swap** if running low on memory:
   ```bash
   sudo dphys-swapfile swapoff
   sudo sed -i 's/CONF_SWAPSIZE=100/CONF_SWAPSIZE=1024/' /etc/dphys-swapfile
   sudo dphys-swapfile setup
   sudo dphys-swapfile swapon
   ```

## Security Recommendations

1. Change default SSH password
2. Use a firewall (ufw)
3. Keep system updated
4. Use HTTPS via reverse proxy
5. Regularly backup your database
