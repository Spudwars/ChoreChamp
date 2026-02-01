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

For production deployment (e.g., on Raspberry Pi):

### Using Gunicorn

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
