# Quickstart: Python Version Quiz

## Prerequisites

- Python 3.12+
- Git

## Setup

```bash
# Clone and enter the project
git clone <repo-url>
cd quizzer

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install django gunicorn whitenoise pytest pytest-django pytest-cov

# Run migrations
python manage.py migrate

# Create admin superuser
python manage.py createsuperuser

# Seed initial quiz content
python manage.py seed_quiz

# Start development server
python manage.py runserver
```

## Usage

1. Visit http://localhost:8000/ to start a quiz
2. Answer 5 questions about Python version features
3. View results with per-question feedback
4. Visit http://localhost:8000/admin/ to manage content

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=quizzer --cov-fail-under=80

# Run specific test files
pytest quizzer/snippetz/tests/test_models.py
pytest quizzer/snippetz/tests/test_services.py
pytest quizzer/snippetz/tests/test_views.py
pytest quizzer/snippetz/tests/test_integration.py
```

## Production Deployment (VPS)

```bash
# Set environment variables
export DJANGO_SECRET_KEY="<generate-a-secret-key>"
export DJANGO_DEBUG=False
export DJANGO_ALLOWED_HOSTS="yourdomain.com"

# Collect static files
python manage.py collectstatic --noinput

# Run migrations
python manage.py migrate

# Seed data (idempotent)
python manage.py seed_quiz

# Start with Gunicorn
gunicorn quizzer.wsgi:application --bind 0.0.0.0:8000
```
