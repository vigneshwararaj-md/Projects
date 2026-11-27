# tutor_project/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Admin panel
    path('admin/', admin.site.urls),
    
    # 🔗 This connects our tutor app's URLs
    # Anything not /admin/ goes to our tutor app
    path('', include('tutor.urls')),
]

# This allows Django to serve uploaded files during development
# MEDIA_URL = '/media/'
# So uploaded PDFs are accessible at: http://127.0.0.1:8000/media/pdfs/filename.pdf
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)