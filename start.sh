#!/bin/bash

# Wait for database to be ready
echo "Waiting for database..."
sleep 5

# Test database connection
echo "Testing database connection..."
python manage.py shell -c "
from django.db import connection
try:
    with connection.cursor() as cursor:
        cursor.execute('SELECT 1')
        print('Database connection successful')
except Exception as e:
    print(f'Database connection failed: {e}')
    exit(1)
"

# Run migrations
echo "Running database migrations..."
python manage.py migrate

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Start the application
echo "Starting application..."
exec gunicorn jorp.wsgi:application --bind 0.0.0.0:$PORT --workers 1 