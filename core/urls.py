"""
Central URL configuration of the Coderr backend.

Every app brings its own urls.py, which gets included here under /api/.
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path

urlpatterns = [
    path('admin/', admin.site.urls),
]

# Serve uploaded files (profile pictures, offer images) during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
