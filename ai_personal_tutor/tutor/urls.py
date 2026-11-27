# tutor/urls.py

from django.urls import path
from . import views

# urlpatterns tells Django: "When someone visits this URL, run this function"
urlpatterns = [
    # Homepage / Dashboard
    # URL: http://127.0.0.1:8000/
    # Runs: views.dashboard
    path('', views.dashboard, name='dashboard'),
    
    # Chat page for a specific document
    # URL: http://127.0.0.1:8000/chat/1/
    # The <int:document_id> captures the number from the URL
    # Runs: views.chat_view
    path('chat/<int:document_id>/', views.chat_view, name='chat'),
    
    # Delete a document
    # URL: http://127.0.0.1:8000/delete/1/
    # Runs: views.delete_document
    path('delete/<int:document_id>/', views.delete_document, name='delete_document'),
]