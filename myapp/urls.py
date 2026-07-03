from django.urls import path
from . import views

urlpatterns = [
    # Connects the root URL to the home function (the dashboard)
    path('', views.home, name='home'),
    
    # Connects the /about/ URL to the about function
    path('about/', views.about, name='about'),
    
    # Connects the hidden /process/ URL for the K-Means algorithm
    path('process/', views.process_csv, name='process'),
]