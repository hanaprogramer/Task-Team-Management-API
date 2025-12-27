# Task Team Management API

Backend API for managing users, teams, projects and tasks  
Built with **Django** + **Django REST Framework**

## Features Implemented So Far

- Custom user model with role and active status
- User registration
- JWT Authentication (login / logout / token refresh)
- Token blacklisting on logout
- Inactive users protection  
  → Users with `is_active=False` cannot login  
  → Custom error message for inactive accounts
- Last login tracking
- Automatic deactivation of inactive users (30 days) via **Celery**
- Admin panel support for user management + visibility of `last_login` & `is_active`

## Authentication Endpoints

| Method | Endpoint                     | Description                          |
|--------|------------------------------|--------------------------------------|
| POST   | `/api/users/register/`       | Register new user                    |
| POST   | `/api/users/login/`          | Login & receive access/refresh tokens|
| POST   | `/api/users/logout/`         | Logout (blacklist current token)     |
| POST   | `/api/token/`                | Obtain new access & refresh tokens   |
| POST   | `/api/token/refresh/`        | Refresh access token                 |

## Development Setup

```bash
# 1. Virtual environment & dependencies
python -m venv venv

# Activate (choose your OS)
source venv/bin/activate          # Linux / macOS
venv\Scripts\activate             # Windows (cmd)
.\venv\Scripts\Activate.ps1       # Windows (PowerShell)

pip install -r requirements.txt
Bash# 2. Apply migrations
python manage.py migrate
Bash# 3. Start development server
python manage.py runserver
Default URL: http://127.0.0.1:8000/
Next Steps / Planned Features

Email activation flow for new users
Full implementation of Teams, Projects & Tasks endpoints
Role-based access control (RBAC)
Comprehensive API test coverage
