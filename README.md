# Cozy Paws

Cozy Paws is an original Django browser game about virtual pets. It does not use third-party brands, copied assets, copied CSS, copied HTML, or copied game text.

## Features

- user registration, login, logout;
- protected gameplay pages;
- player profile with display name and bio;
- virtual pets with level, experience, energy, mood, and hunger;
- pet actions: feed, play, pet, walk;
- passive energy recovery;
- anti-spam cooldowns for active actions;
- beauty, agility, obedience, and charm pet stats;
- hearts as a second non-premium currency;
- coins and item economy;
- shop and inventory;
- wardrobe, wearable shop, equip/unequip/sell flow;
- training actions;
- pet shows with entry fees, scores, medals, and rewards;
- daily quests and rewards;
- achievements and action history;
- friends, private messages, global chat, reports, and support tickets;
- online presence counter;
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

## Docker Run

```powershell
docker compose up --build
```

The app will listen on all local network interfaces:

```text
http://127.0.0.1:8000/
http://<your-lan-ip>:8000/
```

Demo account after the container starts:

```text
login: demo
password: demo12345
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
SUPABASE_AUTH_ENABLED=True
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=<anon-key>
SUPABASE_SERVICE_ROLE_KEY=<service-role-key>
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

## Supabase

Cozy Paws supports Supabase for both infrastructure database and password auth:

- set `DATABASE_URL` to the Supabase Postgres connection string;
- set `SUPABASE_AUTH_ENABLED=True`;
- set `SUPABASE_URL` and `SUPABASE_ANON_KEY`;
- keep Django sessions enabled: Supabase authenticates credentials, then the app mirrors the Supabase user into a local Django user so existing game ownership logic keeps working.

The Docker Compose file reads those variables from the host environment. Without them, it falls back to the local Postgres service for development.

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
