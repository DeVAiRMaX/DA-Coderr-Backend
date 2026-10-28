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

## Project Structure

| App             | Responsibility                                  |
|-----------------|-------------------------------------------------|
| `core`          | Settings and central URL routing                |
| `auth_app`      | Registration, login, guest accounts             |
| `profiles_app`  | User profiles (customer / business)             |
| `offers_app`    | Offers and their three packages (offer details) |
| `orders_app`    | Orders and order counts                         |
| `reviews_app`   | Reviews of business users                       |
| `base_info_app` | Platform statistics                             |

Every app keeps its API code (serializers, views, urls, permissions) in an `api/` folder.

## API Endpoints

All endpoints are prefixed with `/api/`. Authentication uses a token
(`Authorization: Token <token>`), which is returned by registration and login.

| Method                 | Endpoint                                    | Access                                     |
|------------------------|---------------------------------------------|--------------------------------------------|
| POST                   | `registration/`                             | public                                     |
| POST                   | `login/`                                    | public                                     |
| GET, PATCH             | `profile/{user_id}/`                        | authenticated, PATCH only own profile      |
| GET                    | `profiles/business/`                        | authenticated                              |
| GET                    | `profiles/customer/`                        | authenticated                              |
| GET                    | `offers/`                                   | public                                     |
| POST                   | `offers/`                                   | business users                             |
| GET                    | `offers/{id}/`                              | authenticated                              |
| PATCH, DELETE          | `offers/{id}/`                              | creator of the offer                       |
| GET                    | `offerdetails/{id}/`                        | authenticated                              |
| GET                    | `orders/`                                   | authenticated (own orders only)            |
| POST                   | `orders/`                                   | customers                                  |
| PATCH                  | `orders/{id}/`                              | business user of the order (status only)   |
| DELETE                 | `orders/{id}/`                              | admins (staff)                             |
| GET                    | `order-count/{business_user_id}/`           | authenticated                              |
| GET                    | `completed-order-count/{business_user_id}/` | authenticated                              |
| GET                    | `reviews/`                                  | authenticated                              |
| POST                   | `reviews/`                                  | customers, one review per business user    |
| PATCH, DELETE          | `reviews/{id}/`                             | author of the review                       |
| GET                    | `base-info/`                                | public                                     |

## Special Behaviour

- **Profile URL uses the user id:** in `profile/{user_id}/` the id is the id of
  the user, not of the profile. Empty profile fields are returned as `''`, never `null`.
- **Offers need exactly three details:** one `basic`, one `standard` and one
  `premium` package. On PATCH every sent detail is identified by its
  `offer_type` and keeps its id; only the sent fields are changed.
- **Unlimited revisions:** `revisions = -1` means unlimited revisions
  (this is how the frontend sends it).
- **Offer list:** paginated with 6 offers per page (`?page=`, `?page_size=`),
  filterable by `creator_id`, `min_price`, `max_delivery_time`, searchable via
  `search` (title, description) and sortable via `ordering`
  (`updated_at`, `min_price`). Empty query parameters are ignored.
- **Prices** are returned as numbers (e.g. `100.0`), not as strings
  (`COERCE_DECIMAL_TO_STRING = False`).
- **Orders copy the package data** (title, price, features, ...) when they are
  created, so later changes to an offer don't change existing orders.
  Deleting an offer keeps its orders.
- **Order status updates** only accept the field `status`
  (`in_progress`, `completed`, `cancelled`). Any other field returns `400`.
- **Reviews:** a customer can review every business user only once;
  a second review returns `403`. Only `rating` (1–5) and `description` can be changed.
- **File uploads** (profile pictures, offer images) are sent as
  `multipart/form-data` and stored in `media/`. In development (`DEBUG = True`)
  Django serves them under `/media/`.
- **Orders can only be deleted by admins.** Create one with `createsuperuser`.

## Running the Tests

```bash
python manage.py test
```

With coverage report:

```bash
coverage run manage.py test
coverage report
```
