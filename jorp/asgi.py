"""
ASGI config for jorp project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jorp.settings')

django_asgi = get_asgi_application()

try:
    from clova_speech_experiments.realtime_server import app as realtime_app
    from starlette.applications import Starlette
    from starlette.routing import Mount

    application = Starlette(routes=[
        Mount('/realtime', app=realtime_app),
        Mount('/', app=django_asgi),
    ])
except Exception:
    application = django_asgi
