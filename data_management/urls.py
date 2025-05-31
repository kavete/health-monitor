from django.urls import path
from data_management import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path('ward', views.ward_details, name='ward_detail'),
]

# /<slug:ward_slug>/