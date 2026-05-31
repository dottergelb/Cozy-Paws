# Cozy Paws

Cozy Paws is an original Django browser game about virtual pets. It does not use third-party brands, copied assets, copied CSS, copied HTML, or copied game text.

## Features

- user registration, login, logout;
- protected gameplay pages;
- player profile with display name and bio;
- virtual pets with level, experience, energy, mood, and hunger;
- pet actions: feed, play, pet, walk;
- passive energy recovery;
- coins and item economy;
- shop and inventory;
- daily quests and rewards;
- achievements and action history;
- player rating;
- Django admin;
- seed command for demo content;
- responsive mobile-first UI with local static assets.

## Local Run

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_game
python manage.py runserver
```

Open http://127.0.0.1:8000/

Demo account after seeding:

```text
login: demo
password: demo12345
```

On Windows you can run the local helper:

```powershell
.\run_local.ps1
```

## Production Configuration

Copy `.env.example` to `.env` or set equivalent environment variables in your hosting platform.

Required production values:

```text
DJANGO_SECRET_KEY=<long random secret>
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=example.com,www.example.com
DJANGO_CSRF_TRUSTED_ORIGINS=https://example.com,https://www.example.com
DATABASE_URL=postgresql://cozypaws_user:<password>@<host>:5432/cozypaws
```

Recommended production startup:

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py seed_game
gunicorn cozypaws.wsgi:application
```

SQLite is used only as the local fallback when `DATABASE_URL` is not set. Production should use PostgreSQL through `DATABASE_URL`.

Example local PostgreSQL setup:

```sql
CREATE DATABASE cozypaws;
CREATE USER cozypaws_user WITH PASSWORD 'change-me';
GRANT ALL PRIVILEGES ON DATABASE cozypaws TO cozypaws_user;
```

Then set:

```powershell
$env:DATABASE_URL="postgresql://cozypaws_user:change-me@localhost:5432/cozypaws"
python manage.py migrate
python manage.py seed_game
```

## Admin

```powershell
python manage.py createsuperuser
```

Then open `/admin/`.

## Checks

```powershell
python manage.py check
python manage.py test
```
