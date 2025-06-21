from django.urls import path
from data_management import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path('ward/<slug:ward_slug>/', views.ward_details, name='ward_detail'),
    # path("htmx", views.htmx_check, name="htmx_check"),
    # path("htmx_response", views.htmx_response, name="htmx_response"),
    path("dashboard/htmx-dashboard-stats/", views.htmx_dashboard_stats, name="htmx-dashboard-stats"),
    path("dashboard/htmx-ward-conditions/", views.htmx_ward_conditions, name="htmx-ward-conditions"),

    path("dashboard/htmx-charts/", views.dashboard_charts, name="htmx-dashboard-charts"),
    path("dashboard/htmx-charts-json/", views.dashboard_charts_json, name="htmx-dashboard-charts-json"),

    path("ward/<slug:ward_slug>/htmx-patient-vitals/", views.htmx_ward_patient_vitals, name="ward-patient-vitals"),
    path("ward/<slug:ward_slug>/htmx-ward-status/", views.htmx_ward_status, name="ward-status"),
    path("ward/<slug:ward_slug>/chart-data/", views.ward_chart_data, name="ward-chart-data"),

    # Patient URLs
    path('patient/<int:patient_id>/', views.patient_details, name='patient_detail'),
    path('patient/<int:patient_id>/vitals-status/', views.htmx_patient_vitals_status, name='patient-vitals-status'),
    path('patient/<int:patient_id>/chart-data/', views.patient_chart_data, name='patient-chart-data'),

]
