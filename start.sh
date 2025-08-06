#!/bin/bash

# Wait for database to be ready
echo "Waiting for database..."
sleep 5

# Run migrations
echo "Running database migrations..."
python manage.py migrate

# Start the application
echo "Starting application..."
exec gunicorn jorp.wsgi:application --bind 0.0.0.0:$PORT --workers 1 