"""
ASGI config for core project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

application = get_asgi_application()
# System auto-createsuperuser script for Render Free Tier
from django.contrib.auth import get_user_model
try:
    User = get_user_model()
    # Check if your email is already registered
    if User.objects.filter(email='remad13579@gmail.com').exists():
        user = User.objects.get(email='remad13579@gmail.com')
        user.is_superuser = True
        user.is_staff = True
        user.save()
        print("Successfully promoted remad13579@gmail.com to Admin!")
    else:
        # If it doesn't exist yet, create it fresh
        User.objects.create_superuser('admin', 'remad13579@gmail.com', 'admin12345')
        print("Created fresh superuser: admin / admin12345")
except Exception as e:
    print("Admin auto-setup log:", e)
