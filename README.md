# ChoreChamp

A family chore tracking and allowance management web application. Children log their completed chores via a simple PIN-based login, and parents can manage chores, track progress, and handle weekly payments.

## Features

- **Child-friendly PIN login** - Kids tap their name and enter a 4-digit PIN
- **Weekly chore calendar** - Visual grid showing all chores for the week
- **Multiple chore frequencies**:
  - Daily (once per day)
  - Twice daily (AM/PM, e.g., teeth brushing)
  - Weekly (once per week)
  - Flexible (X times per week on any days)
  - Specific days (e.g., piano practice on Mon/Sat only)
  - Ad-hoc (one-time chores)
- **Real-time updates** - HTMX-powered checkboxes update instantly
- **Progress tracking** - Visual progress bars for each chore
- **Allowance calculation** - Base allowance + chore earnings
- **User-specific chores** - Assign chores to specific children or all
- **Ad-hoc chores** - Children can add extra chores they've done
- **Admin dashboard** - Parents can manage chores, users, and payments
- **Email notifications** - Weekly summaries and payment confirmations
- **Date override** - Admin can test with different dates

## Tech Stack

- **Backend**: Python 3.9+, Flask 3.0
- **Database**: SQLite (easily swappable to PostgreSQL)
- **Frontend**: Jinja2 templates, HTMX, Alpine.js, Tailwind CSS
- **Authentication**: Flask-Login (PIN for kids, password for adults)
- **Email**: Flask-Mail with Gmail SMTP

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/Spudwars/ChoreChamp.git
cd ChoreChamp
```

### 2. Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/macOS
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Create Environment File

Create a `.env` file in the project root:

```bash
# Required
SECRET_KEY=your-secret-key-change-this-in-production
JWT_SECRET_KEY=your-jwt-secret-change-this-in-production

# Optional: Database (defaults to SQLite in instance/chorechamp.db)
# DATABASE_URL=sqlite:///instance/chorechamp.db

# Optional: Email Configuration (for notifications)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=ChoreChamp <your-email@gmail.com>
```

### 5. Initialize Database

```bash
flask init-db
flask seed
```

This creates the database tables and adds sample data.

### 6. Run the Application

```bash
# Development
python run.py

# Or using Flask CLI
flask run --host=0.0.0.0 --port=5000
```

The app will be available at `http://localhost:5000`

## Default Users

After running `flask seed`, these accounts are created:

| User | Type | Login | Credentials |
|------|------|-------|-------------|
| Parent | Admin | Email/Password | `admin@chorechamp.local` / `password123` |
| Emma | Child | PIN | `1234` |
| Jack | Child | PIN | `5678` |

## Email Configuration (Gmail)

To enable email notifications, you need to set up Gmail with an App Password:

1. **Enable 2-Step Verification** on your Google Account:
   - Go to [Google Account Security](https://myaccount.google.com/security)
   - Enable "2-Step Verification"

2. **Create an App Password**:
   - Go to [App Passwords](https://myaccount.google.com/apppasswords)
   - Select "Mail" and your device
   - Click "Generate"
   - Copy the 16-character password

3. **Update your `.env` file**:
   ```bash
   MAIL_SERVER=smtp.gmail.com
   MAIL_PORT=587
   MAIL_USE_TLS=true
   MAIL_USERNAME=your-email@gmail.com
   MAIL_PASSWORD=xxxx-xxxx-xxxx-xxxx  # App password (not your regular password)
   MAIL_DEFAULT_SENDER=ChoreChamp <your-email@gmail.com>
   ```

4. **Test the configuration**:
   - Log in as admin
   - Click "Send Test Email" on the admin dashboard
   - Check your inbox for the weekly summary

Emails are sent:
- **Automatically**: Weekly summary every Sunday at 7pm
- **On payment**: Confirmation when a payment is marked as paid
- **Manually**: Via "Send Test Email" button in admin panel

## Mobile App (PWA)

ChoreChamp is a Progressive Web App (PWA) that can be installed on phones and tablets for a native app-like experience.

### Installing on Android

1. Open ChoreChamp in Chrome
2. Tap the "Install" prompt that appears, OR
3. Tap the three-dot menu → "Add to Home Screen"
4. The app will appear on your home screen with the ChoreChamp icon

### Installing on iPhone/iPad

1. Open ChoreChamp in Safari
2. Tap the Share button (square with arrow)
3. Scroll down and tap "Add to Home Screen"
4. Tap "Add" in the top right
5. The app will appear on your home screen

### PWA Features

- **Offline viewing**: View your dashboard even without internet
- **Home screen icon**: Quick access like a native app
- **Full screen**: No browser address bar
- **Install prompt**: Users are prompted to install automatically

### Regenerating Icons

If you want to customize the app icons:

```bash
# Edit generate_icons.py to change colors/design
python generate_icons.py
```

Icons are generated at sizes: 72, 96, 128, 144, 152, 192, 384, and 512 pixels.

## Project Structure

```
chorechamp/
├── app/
│   ├── __init__.py          # Flask app factory
│   ├── config.py            # Configuration classes
│   ├── models/              # SQLAlchemy models
│   │   ├── user.py          # User (children + adults)
│   │   ├── chore.py         # Chore definitions
│   │   ├── chore_log.py     # Completion records
│   │   └── week.py          # Week periods + payments
│   ├── routes/              # Flask blueprints
│   │   ├── auth.py          # Login/logout
│   │   ├── dashboard.py     # Child dashboard
│   │   ├── admin.py         # Admin panel
│   │   └── api.py           # REST API (for future mobile app)
│   ├── services/            # Business logic
│   │   ├── allowance_service.py
│   │   ├── email_service.py
│   │   └── scheduler_service.py
│   ├── templates/           # Jinja2 templates
│   └── static/              # CSS, JS, images
├── tests/                   # pytest tests
├── instance/                # SQLite database (created on init)
├── run.py                   # Entry point
├── requirements.txt         # Python dependencies
└── .env                     # Environment variables (create this)
```

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_models/test_allowance.py -v
```

## Production Deployment

### Docker Deployment (Recommended for Raspberry Pi)

The easiest way to deploy ChoreChamp on a Raspberry Pi is using Docker. This section provides step-by-step instructions for deploying to `adsb.mi`.

#### Prerequisites

Ensure Docker and Docker Compose are installed on your Pi:

```bash
# SSH into your Pi
ssh pi@adsb.mi

# Check if Docker is installed
docker --version

# If not installed, run:
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
sudo apt install docker-compose -y

# Log out and back in for group changes
exit
ssh pi@adsb.mi
```

#### Step 1: Clone the Repository

SSH into your Pi and clone from GitHub:

```bash
ssh pi@adsb.mi
git clone https://github.com/Spudwars/ChoreChamp.git ~/chorechamp
```

#### Step 2: Create Environment File

SSH into your Pi and create the `.env` file:

```bash
ssh pi@adsb.mi
cd ~/chorechamp
nano .env
```

Add the following configuration:

```bash
# ===========================================
# REQUIRED SETTINGS - You MUST change these
# ===========================================

# SECRET_KEY: Used for session encryption and CSRF protection
# Requirements: Any random string, minimum 32 characters recommended
# Generate one with: python3 -c "import secrets; print(secrets.token_hex(32))"
# Example: a1b2c3d4e5f6... (64 hex characters)
SECRET_KEY=CHANGE_ME_generate_a_random_64_character_hex_string

# JWT_SECRET_KEY: Used for API token signing (can be same format as SECRET_KEY)
# Generate one with: python3 -c "import secrets; print(secrets.token_hex(32))"
JWT_SECRET_KEY=CHANGE_ME_generate_another_random_64_character_hex_string

# ===========================================
# OPTIONAL: Settings Encryption Key
# ===========================================
# Used to encrypt sensitive settings stored in database (like email passwords)
# If not set, derives from SECRET_KEY automatically
# SETTINGS_ENCRYPTION_KEY=

# ===========================================
# OPTIONAL: Email Configuration
# ===========================================
# Can also be configured via Admin UI after first login
# MAIL_SERVER=smtp.gmail.com
# MAIL_PORT=587
# MAIL_USE_TLS=True
# MAIL_USERNAME=your.email@gmail.com
# MAIL_PASSWORD=your-16-char-app-password
# MAIL_DEFAULT_SENDER=ChoreChamp <your.email@gmail.com>
```

**Important: Generate your secret keys!** Run this on the Pi to generate them:

```bash
# Generate SECRET_KEY
python3 -c "import secrets; print('SECRET_KEY=' + secrets.token_hex(32))"

# Generate JWT_SECRET_KEY
python3 -c "import secrets; print('JWT_SECRET_KEY=' + secrets.token_hex(32))"
```

Copy the output and paste into your `.env` file.

Save and exit nano: `Ctrl+X`, then `Y`, then `Enter`

#### Step 3: Build and Start the Container

```bash
cd ~/chorechamp

# Build the Docker image (takes a few minutes on Pi)
docker-compose build

# Start the container in background
docker-compose up -d

# Check it's running
docker ps
```

#### Step 4: Access ChoreChamp

Open a browser and go to: **http://adsb.mi:5001**

On first run, the database will be empty. You can either:

1. **Create users manually** via the login page (first admin must be created via CLI)
2. **Seed sample data** (recommended for testing):

```bash
# Enter the running container
docker exec -it chorechamp bash

# Inside container, seed the database
cd /app
python -c "
from app import create_app, db
from app.models.user import User

app = create_app()
with app.app_context():
    # Create admin user
    admin = User(name='Parent', email='admin@chorechamp.local', is_admin=True)
    admin.set_password('password123')
    db.session.add(admin)

    # Create sample children
    emma = User(name='Emma', is_admin=False, base_allowance=2.0)
    emma.set_pin('1234')
    db.session.add(emma)

    jack = User(name='Jack', is_admin=False, base_allowance=2.0)
    jack.set_pin('5678')
    db.session.add(jack)

    db.session.commit()
    print('Users created!')
"

# Exit container
exit
```

#### Updating ChoreChamp

To update to the latest version, run this single command:

```bash
cd ~/chorechamp && ./update.sh
```

Or if you prefer to run the steps manually:

```bash
cd ~/chorechamp
git pull origin main
docker-compose down
docker-compose build
docker-compose up -d
docker exec chorechamp python /app/migrate.py
```

The update script:
1. Pulls the latest code from GitHub
2. Rebuilds the Docker container with new code
3. Restarts the service
4. Runs any required database migrations
5. **Your database and settings are preserved** - only the code is updated

#### Quick Reference Commands

```bash
# Update to latest version
cd ~/chorechamp && ./update.sh

# View logs
docker-compose logs -f

# Restart the container
docker-compose restart

# Stop the container
docker-compose down

# Backup database
cp ~/chorechamp/instance/chorechamp.db ~/backups/chorechamp-$(date +%Y%m%d).db
```

#### Configuration Reference

| Setting | Required | Format | Description |
|---------|----------|--------|-------------|
| `SECRET_KEY` | Yes | 32+ character hex string | Session encryption. Generate with `secrets.token_hex(32)` |
| `JWT_SECRET_KEY` | Yes | 32+ character hex string | API token signing. Generate with `secrets.token_hex(32)` |
| `SETTINGS_ENCRYPTION_KEY` | No | Fernet key (auto-derived if not set) | Encrypts email password in database |
| `MAIL_SERVER` | No | Hostname | SMTP server (e.g., `smtp.gmail.com`) |
| `MAIL_PORT` | No | Number | SMTP port (usually `587` for TLS) |
| `MAIL_USE_TLS` | No | `True`/`False` | Enable TLS encryption |
| `MAIL_USERNAME` | No | Email address | SMTP login username |
| `MAIL_PASSWORD` | No | String | SMTP password (use App Password for Gmail) |
| `MAIL_DEFAULT_SENDER` | No | `Name <email>` | From address for emails |

#### Troubleshooting

**Container won't start:**
```bash
# Check logs for errors
docker-compose logs

# Common fix: ensure instance directory exists
mkdir -p ~/chorechamp/instance
```

**Can't access http://adsb.mi:5001:**
```bash
# Check container is running
docker ps

# Check port is open
sudo netstat -tlnp | grep 5001

# Try accessing locally on Pi
curl http://localhost:5001
```

**Database errors after update:**
```bash
# Run migrations manually
docker exec chorechamp python /app/migrate.py
```

---

### Manual Deployment (Without Docker)

For production deployment without Docker:

#### Using Gunicorn

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 run:app
```

### Using systemd Service

Create `/etc/systemd/system/chorechamp.service`:

```ini
[Unit]
Description=ChoreChamp
After=network.target

[Service]
User=pi
WorkingDirectory=/home/pi/ChoreChamp
Environment="PATH=/home/pi/ChoreChamp/venv/bin"
EnvironmentFile=/home/pi/ChoreChamp/.env
ExecStart=/home/pi/ChoreChamp/venv/bin/gunicorn -w 2 -b 0.0.0.0:5000 run:app
Restart=always

[Install]
WantedBy=multi-user.target
```

Then enable and start:

```bash
sudo systemctl enable chorechamp
sudo systemctl start chorechamp
```

### Nginx Reverse Proxy (Optional)

```nginx
server {
    listen 80;
    server_name chorechamp.local;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## API Endpoints

REST API available for future mobile app integration:

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/login` | JWT authentication |
| GET | `/api/v1/weeks/current` | Get current week data |
| POST | `/api/v1/chores/<id>/complete` | Mark chore complete |

## CLI Commands

```bash
flask init-db    # Create database tables
flask seed       # Add sample users and chores
flask shell      # Interactive Python shell with app context
```

## License

MIT License - feel free to use and modify for your family!

## Contributing

Pull requests welcome! Please ensure tests pass before submitting.
