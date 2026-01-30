# 🎓 ScholarNode Backend - School Management System

A robust Django REST Framework backend for managing school operations including student enrollment, teacher management, payments, and notifications.

![Django](https://img.shields.io/badge/django-6.0.1-green.svg)
![Python](https://img.shields.io/badge/python-3.11-blue.svg)
![DRF](https://img.shields.io/badge/DRF-3.16.1-red.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

## 📋 Table of Contents
- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Prerequisites](#-prerequisites)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Running the Application](#-running-the-application)
- [API Documentation](#-api-documentation)
- [Security](#-security)
- [Deployment](#-deployment)
- [Contributing](#-contributing)

## ✨ Features

- 🔐 **Clerk Authentication** - Secure user authentication with Clerk
- 👥 **User Management** - Student and Teacher role-based access control
- 💳 **Payment Processing** - Integrated Stripe payment system
- 📧 **Email Notifications** - Automated email system using Resend/SMTP
- 📁 **Cloud Storage** - Cloudinary integration for media files
- 🔄 **Async Tasks** - Celery with Redis for background jobs
- 📊 **API Documentation** - Auto-generated with drf-spectacular
- 🛡️ **Security First** - HTTPS, HSTS, CSRF, CORS protection
- 📝 **Comprehensive Logging** - Structured logging for debugging
- 🎨 **Rate Limiting** - DDoS protection with throttling

## 🛠 Tech Stack

- **Framework:** Django 6.0.1
- **API:** Django REST Framework 3.16.1
- **Database:** PostgreSQL (Neon)
- **Cache/Queue:** Redis
- **Task Queue:** Celery 5.6.2
- **Authentication:** Clerk + JWT
- **Payment:** Stripe
- **Storage:** Cloudinary
- **Email:** Resend / Gmail SMTP

## 📦 Prerequisites

- Python 3.11+
- PostgreSQL 13+ (or Neon account)
- Redis 7+
- Docker & Docker Compose (optional)
- Git

## 🚀 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/scholarnode-backend.git
cd scholarnode-backend
```

### 2. Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Environment Configuration

```bash
# Copy example environment file
cp .env.example .env

# Generate a secure SECRET_KEY
python apps/common/security.py

# Edit .env with your actual credentials
# NEVER use the example values in production!
```

## ⚙️ Configuration

### Required Environment Variables

Edit your `.env` file with the following:

```bash
# Django Core
SECRET_KEY=your-generated-secret-key-here
DEBUG=False
DJANGO_SETTINGS_MODULE=config.settings.prod
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Database (Neon PostgreSQL)
DATABASE_URL=postgresql://user:password@host:port/dbname?sslmode=require

# Redis & Celery
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Clerk Authentication
CLERK_SECRET_KEY=sk_test_...
CLERK_PUBLISHABLE_KEY=pk_test_...
CLERK_WEBHOOK_SECRET=whsec_...

# Cloudinary
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret

# Stripe
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Email
RESEND_API_KEY=re_...
# OR use Gmail SMTP
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Frontend
FRONTEND_URL=https://yourfrontend.com

# Security
CSRF_TRUSTED_ORIGINS=https://yourdomain.com
CORS_ALLOWED_ORIGINS=https://yourfrontend.com
```

### Generate Secure Keys

```bash
python apps/common/security.py
```

This will generate:
- Django SECRET_KEY
- API Keys
- Webhook Secrets

## 🏃 Running the Application

### Development Mode

```bash
# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic --noinput

# Run development server
python manage.py runserver
```

### Using Docker Compose

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

### Production Mode

```bash
# Set environment
export DJANGO_SETTINGS_MODULE=config.settings.prod

# Run with gunicorn (recommended)
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 4

# Or use uvicorn for ASGI
uvicorn config.asgi:application --host 0.0.0.0 --port 8000 --workers 4
```

### Celery Worker

```bash
# Start Celery worker
celery -A config worker -l info

# Start Celery beat (for scheduled tasks)
celery -A config beat -l info

# Start both together
celery -A config worker -B -l info
```

## 📚 API Documentation

### Interactive API Docs

Once running, visit:
- **Swagger UI:** http://localhost:8000/api/schema/swagger-ui/
- **ReDoc:** http://localhost:8000/api/schema/redoc/
- **OpenAPI Schema:** http://localhost:8000/api/schema/

### Admin Panel

Access Django admin at:
- **URL:** http://localhost:8000/admin/
- **Note:** Change `ADMIN_URL` in `.env` for production security

### Main API Endpoints

```
Authentication:
  POST   /api/auth/webhook/         - Clerk webhook handler
  POST   /api/auth/login/           - Login endpoint
  POST   /api/auth/logout/          - Logout endpoint

Users:
  GET    /api/users/                - List users
  GET    /api/users/{id}/           - User detail
  PUT    /api/users/{id}/           - Update user
  DELETE /api/users/{id}/           - Delete user

Students:
  GET    /api/students/             - List students
  POST   /api/students/             - Create student
  GET    /api/students/{id}/        - Student detail
  PUT    /api/students/{id}/        - Update student

Teachers:
  GET    /api/teachers/             - List teachers
  POST   /api/teachers/             - Create teacher
  GET    /api/teachers/{id}/        - Teacher detail

Payments:
  POST   /api/payments/create/      - Create payment intent
  POST   /api/payments/webhook/     - Stripe webhook
  GET    /api/payments/history/     - Payment history

Notifications:
  GET    /api/notifications/        - List notifications
  POST   /api/notifications/        - Create notification
  PATCH  /api/notifications/{id}/   - Mark as read
```

## 🔒 Security

### Security Checklist

- [x] Strong SECRET_KEY (50+ chars)
- [x] DEBUG = False in production
- [x] HTTPS/SSL enforced
- [x] HSTS enabled with preload
- [x] Secure cookies (HttpOnly, Secure, SameSite)
- [x] CSRF protection enabled
- [x] CORS properly configured
- [x] Rate limiting enabled
- [x] SQL injection protection (ORM)
- [x] XSS protection headers
- [x] Password hashing (Argon2)
- [x] Environment variables secured
- [x] Secrets rotation policy

### Security Best Practices

1. **Never commit `.env` files** to version control
2. **Rotate secrets** every 90 days
3. **Use strong passwords** (min 10 characters)
4. **Enable 2FA** for admin accounts
5. **Regular security audits:**
   ```bash
   pip install safety
   safety check
   ```
6. **Monitor logs** for suspicious activity
7. **Keep dependencies updated:**
   ```bash
   pip list --outdated
   ```

### Reporting Security Issues

Please report security vulnerabilities to: **security@yourdomain.com**

See [SECURITY.md](SECURITY.md) for details.

## 🚀 Deployment

### Deployment Checklist

Before deploying to production:

- [ ] Set `DEBUG=False`
- [ ] Configure `ALLOWED_HOSTS` with your domain
- [ ] Set `DJANGO_SETTINGS_MODULE=config.settings.prod`
- [ ] Generate strong `SECRET_KEY`
- [ ] Configure production database (Neon PostgreSQL)
- [ ] Set up Redis for caching/Celery
- [ ] Configure Cloudinary for media storage
- [ ] Set up proper CORS/CSRF origins
- [ ] Enable HTTPS/SSL
- [ ] Configure email service
- [ ] Set up monitoring (Sentry, etc.)
- [ ] Configure backup strategy
- [ ] Set up CI/CD pipeline

### Deployment Platforms

This project can be deployed to:
- **Railway** (Recommended)
- **Render**
- **Heroku**
- **DigitalOcean App Platform**
- **AWS Elastic Beanstalk**
- **Google Cloud Run**
- **Azure App Service**

### Example: Deploy to Railway

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Initialize project
railway init

# Add environment variables
railway variables set SECRET_KEY=your-secret-key
railway variables set DEBUG=False
# ... add all other variables

# Deploy
railway up
```

## 🧪 Testing

```bash
# Run all tests
python manage.py test

# Run with coverage
coverage run --source='.' manage.py test
coverage report
coverage html

# Run specific app tests
python manage.py test apps.users
python manage.py test apps.students
```

## 📊 Database Migrations

```bash
# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Show migration status
python manage.py showmigrations

# Rollback migration
python manage.py migrate app_name migration_name
```

## 🔧 Useful Commands

```bash
# Create superuser
python manage.py createsuperuser

# Shell with Django context
python manage.py shell

# Database shell
python manage.py dbshell

# Clear cache
python manage.py clear_cache

# Export requirements
pip freeze > requirements.txt

# Check for issues
python manage.py check

# Collect static files
python manage.py collectstatic --noinput
```

## 📝 Project Structure

```
backend/
├── apps/
│   ├── auth/              # Authentication & Clerk integration
│   ├── common/            # Shared utilities & middleware
│   ├── users/             # User model & management
│   ├── students/          # Student management
│   ├── teachers/          # Teacher management
│   ├── payments/          # Stripe payment processing
│   ├── notifications/     # Email & push notifications
│   ├── webhooks/          # Webhook handlers
│   └── settings/          # App-level settings
├── config/
│   ├── settings/
│   │   ├── base.py       # Base settings
│   │   ├── dev.py        # Development settings
│   │   └── prod.py       # Production settings
│   ├── urls.py           # URL routing
│   ├── wsgi.py           # WSGI application
│   ├── asgi.py           # ASGI application
│   └── celery.py         # Celery configuration
├── logs/                 # Application logs
├── media/                # User uploaded files (local backup)
├── static/               # Static files
├── staticfiles/          # Collected static files
├── .env.example          # Environment template
├── .gitignore           # Git ignore rules
├── requirements.txt      # Python dependencies
├── docker-compose.yml    # Docker configuration
├── Dockerfile           # Docker build file
├── manage.py            # Django management script
└── README.md            # This file
```

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Coding Standards

- Follow PEP 8 style guide
- Write meaningful commit messages
- Add docstrings to functions/classes
- Write tests for new features
- Update documentation

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👥 Authors

- **Your Name** - *Initial work* - [YourGitHub](https://github.com/yourusername)

## 🙏 Acknowledgments

- Django & DRF communities
- Clerk for authentication
- Stripe for payment processing
- Cloudinary for media storage
- All contributors

## 📞 Support

For support, email support@yourdomain.com or join our Slack channel.

## 🔗 Links

- [Documentation](https://docs.yourdomain.com)
- [API Reference](https://api.yourdomain.com/docs)
- [Change Log](CHANGELOG.md)
- [Security Policy](SECURITY.md)

---

**⚠️ IMPORTANT SECURITY NOTICE:**
- Never commit `.env` files to version control
- Always use strong, randomly generated secrets
- Keep dependencies updated
- Enable all security features in production
- Regularly audit your security posture

Made with ❤️ by ScholarNode Team
