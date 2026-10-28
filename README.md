# Coderr Backend

REST API for the Coderr freelancer platform, built with Django and Django REST Framework.
Business users offer services in three packages (basic, standard, premium), customers order them and leave reviews.

The frontend is provided separately and is **not** part of this repository.

## Tech Stack

- Python 3.14
- Django 5.2
- Django REST Framework (token authentication)
- django-cors-headers, django-filter
- SQLite (development)

## Getting Started

1. Clone the repository

   ```bash
   git clone https://github.com/DeVAiRMaX/DA-Coderr-Backend.git
   cd DA-Coderr-Backend
   ```

2. Create and activate a virtual environment

   ```bash
   python3 -m venv venv
   source venv/bin/activate        # Windows: venv\Scripts\activate
   ```

3. Install the dependencies

   ```bash
   pip install -r requirements.txt
   ```

4. Apply the migrations (this also creates the guest accounts, see below)

   ```bash
   python manage.py migrate
   ```

5. Optional: create an admin account for the Django admin (`/admin/`)

   ```bash
   python manage.py createsuperuser
   ```

6. Start the development server

   ```bash
   python manage.py runserver
   ```

The API is now available at `http://127.0.0.1:8000/api/`.

## Guest Accounts

The frontend offers a guest login for both user types. These accounts are
created automatically by a data migration (`auth_app/migrations/0001_create_guest_users.py`)
when running `migrate`:

| Type     | Username | Password   |
|----------|----------|------------|
| customer | `andrey` | `asdasd`   |
| business | `kevin`  | `asdasd24` |

## Frontend

Open the frontend with VS Code **Live Server** (default: `http://127.0.0.1:5500`).
This origin is allowed via CORS in `core/settings.py`.
If your Live Server runs on another port, add it to `CORS_ALLOWED_ORIGINS`.

## Running the Tests

```bash
python manage.py test
```

With coverage report:

```bash
coverage run manage.py test
coverage report
```
