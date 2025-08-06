#!/usr/bin/env bash
# Start script for deployment
exec gunicorn jorp.wsgi:application --bind 0.0.0.0:$PORT --workers 1 