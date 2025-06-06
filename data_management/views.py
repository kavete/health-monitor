from django.shortcuts import get_object_or_404, render
from .models import Ward, Patient, Doctor, Microcontroller, Bed, WardReading, PatientVitals
from django.db.models import Max
from django.utils.timezone import now
from django.http import JsonResponse
import json

def get_dashboard_stats():
    return {
        'ward_count': Ward.objects.count(),
        'patient_count': Patient.objects.count(),
        'doctor_count': Doctor.objects.count(),
        'bed_count': Bed.objects.count(),
        'microcontroller_count': Microcontroller.objects.count(),
    }


def get_latest_ward_conditions():
    latest_per_ward = (
        WardReading.objects.values('ward')
        .annotate(latest=Max('timestamp'))
    )
    # Build a list of latest WardCondition objects for each ward
    latest_conditions = [
        WardReading.objects.filter(ward=entry['ward'], timestamp=entry['latest']).first()
        for entry in latest_per_ward
    ]
    return latest_conditions

def get_chart_data():
    latest_conditions = get_latest_ward_conditions()
    wards  = []
    temperature =[]
    humidity = []

    for condition in latest_conditions:
        if condition:  # Check if condition is not None
            wards.append(condition.ward.name)
            temperature.append(float(condition.temperature) if condition.temperature else 0)
            humidity.append(float(condition.humidity) if condition.humidity else 0)
    return  {
        'chart_wards': json.dumps(wards),
        'chart_temperature': json.dumps(temperature),
        'chart_humidity': json.dumps(humidity),
    }

def dashboard(request):
    stats= get_dashboard_stats()
    latest_conditions = get_latest_ward_conditions()
    comparison_chart_data = get_chart_data()
    context = {
        'ward_conditions': latest_conditions,
        **stats,
        **comparison_chart_data,
    }


    return render(request, 'data_management/index.html', context)

def dashboard_charts(request): 
    comparison_chart_data = get_chart_data()

    context = {
        **comparison_chart_data,
    }
    return render(request, "data_management/snippets/ward-comparison.html", context)

def dashboard_charts_json(request):
    comparison_chart_data = get_chart_data()
    # Parse the JSON strings back to objects for the JSON response
    return JsonResponse({
        'wards': json.loads(comparison_chart_data['chart_wards']),
        'temperature': json.loads(comparison_chart_data['chart_temperature']),
        'humidity': json.loads(comparison_chart_data['chart_humidity']),
    })


def ward_details(request, ward_slug):
    ward = get_object_or_404(Ward, slug=ward_slug)
    latest_condition = WardReading.objects.filter(ward=ward).order_by('-timestamp').first()
    patients_in_ward = Patient.objects.filter(bed__ward=ward).select_related('bed')

    patient_vitals = []
    for patient in patients_in_ward:
        latest_vital = PatientVitals.objects.filter(patient=patient).order_by('-timestamp').first()
        if latest_vital:
            patient_vitals.append(latest_vital)
    context = {
        'ward_name': ward.name,
        'ward_slug': ward.slug,
        'latest_condition': latest_condition,
        "patient_vitals": patient_vitals,
    }
    
    return render(request, 'data_management/ward-details.html', context)


def htmx_check(request):
    return render(request, 'data_management/htmx-check.html')


def htmx_response(request):
    current_time = now().strftime("%H:%M:%S")
    context = {
        'current_time': current_time,
    }
    return render(request, 'data_management/snippets/htmx-response.html', context)


def htmx_dashboard_stats(request):
    stats = get_dashboard_stats()
    context = {
        **stats,
    }
    return render(request, 'data_management/snippets/dashboard-stats.html', context)


def htmx_ward_conditions(request):
    latest_condition = get_latest_ward_conditions()
    context = {
        'ward_conditions': latest_condition,
    }
    return render(request, 'data_management/snippets/ward-conditions.html', context)
