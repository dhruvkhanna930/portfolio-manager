# New Portfolio Management System

A cleanly organized Django-based portfolio management application with separate backend and frontend directories.

## Structure

- backend/ - Django project and application code
- frontend/ - templates and static assets served by Django

## Run locally

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```
