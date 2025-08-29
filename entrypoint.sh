set -e
python manage.py collectstatic --noinput 2>/dev/null || true
python manage.py migrate --noinput
exec daphne -b 0.0.0.0 -p 8000 config.asgi:application