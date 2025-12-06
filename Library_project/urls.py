"""
URL configuration for the Library_project Django project.
"""

from django.conf import settings # new
from django.conf.urls.static import static # new
from django.contrib import admin
from django.urls import path,include # new

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("library_web.urls")), # new
]

if settings.DEBUG or not settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
