from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),          # Loads index.html
    path('about/', views.about_view, name='about'),  # Loads about.html
    path('process/', views.process_csv, name='process_csv'), # The hidden backend API
]