# Docker

The default Compose setup runs NutriHub with PostgreSQL 16 and Gunicorn.
The database data is stored in a Docker volume.

```bash
docker compose up --build -d
docker compose exec web python manage.py createsuperuser
```

Open `http://localhost:8000/`.

Set a real secret before starting the stack:

```bash
export DJANGO_SECRET_KEY="$(python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')"
export DJANGO_ALLOWED_HOSTS="localhost,127.0.0.1"
docker compose up --build -d
```

For SQLite instead of PostgreSQL, set `DATABASE_URL=sqlite:///db.sqlite3` when
running Django locally. Docker Compose is PostgreSQL-based.

Before production deployment:

- replace `DJANGO_SECRET_KEY`;
- set `DJANGO_DEBUG=False`;
- add the public domain to `DJANGO_ALLOWED_HOSTS`;
- use PostgreSQL or a managed database;
- configure persistent media storage;
- configure HTTPS and a reverse proxy;
- collect static assets;
- use immutable container secrets.
