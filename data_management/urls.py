from django.urls import path
from data_management import views

urlpatterns = [
    path("", views.dashboard, name="dashboard")
]
