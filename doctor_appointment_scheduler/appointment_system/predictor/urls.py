from django.urls import path
from . import views

urlpatterns = [
    path('test/', views.test_predictor, name='test_predictor'),
    path('stats/', views.dashboard_stats, name='predictor_stats'),
]