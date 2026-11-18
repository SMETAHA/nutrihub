# Docker

The default Compose setup runs NutriHub with a SQLite database mounted through the
project directory. This setup is intended for local demonstration and development,
not for a high-availability production deployment.

```bash
docker compose up --build -d
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser
```

Open `http://localhost:8000/`.

Before production deployment:

- replace `DJANGO_SECRET_KEY`;
- set `DJANGO_DEBUG=False`;
- add the public domain to `DJANGO_ALLOWED_HOSTS`;
- use PostgreSQL or a managed database;
- configure persistent media storage;
- configure HTTPS and a reverse proxy;
- collect static assets;
- use immutable container secrets.
