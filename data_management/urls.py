from django.urls import path
from data_management import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path('ward/<slug:ward_slug>/', views.ward_details, name='ward_detail'),
    # path("htmx", views.htmx_check, name="htmx_check"),
    # path("htmx_response", views.htmx_response, name="htmx_response"),
    path("htmx-dashboard_stats", views.htmx_dashboard_stats, name="htmx-dashboard-stats"),
    path("htmx-ward-conditions", views.htmx_ward_conditions, name="htmx-ward-conditions"),
]
