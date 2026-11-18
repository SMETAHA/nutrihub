# Contributing to NutriHub

Thank you for contributing to NutriHub.

## Development setup

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py runserver
```

## Before a pull request

```bash
python manage.py check
python manage.py test
ruff check .
black --check .
isort --check-only .
```

## Guidelines

- Keep changes focused and include tests for behavioral changes.
- Do not commit `.venv`, SQLite databases, media, secrets or local IDE settings.
- Use migrations for model changes.
- Escape template output and preserve Django authorization checks.
- Keep user-facing text consistent and accessible.

## Pull request checklist

- [ ] Changes are covered by tests where practical.
- [ ] Django checks pass.
- [ ] No secrets or personal data are included.
- [ ] Database migrations are included when needed.
- [ ] Documentation is updated for user-visible changes.
