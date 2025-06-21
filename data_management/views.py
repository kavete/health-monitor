from django.shortcuts import get_object_or_404, render
from .models import Ward, Patient, Doctor, Microcontroller, Bed, WardReading, PatientVitals
from django.db.models import Max
from django.http import JsonResponse
from django.utils import timezone
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
    noise = []
    light_intensity = []

    for condition in latest_conditions:
        if condition:  # Check if condition is not None
            wards.append(condition.ward.name)
            temperature.append(float(condition.temperature) if condition.temperature else 0)
            humidity.append(float(condition.humidity) if condition.humidity else 0)
            noise.append(float(condition.noise_level) if condition.noise_level else 0)
            light_intensity.append(float(condition.light_intensity) if condition.light_intensity else 0)
    return  {
        'chart_wards': json.dumps(wards),
        'chart_temperature': json.dumps(temperature),
        'chart_humidity': json.dumps(humidity),
        'chart_noise': json.dumps(noise),
        'chart_light_intensity': json.dumps(light_intensity),
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
    return JsonResponse({
        'wards': json.loads(comparison_chart_data['chart_wards']),
        'temperature': json.loads(comparison_chart_data['chart_temperature']),
        'humidity': json.loads(comparison_chart_data['chart_humidity']),
        'noise': json.loads(comparison_chart_data['chart_noise']),
        'light_intensity': json.loads(comparison_chart_data['chart_light_intensity']),
    })

def get_patient_vitals_data(ward):
    """
    Returns a list of the latest PatientVitals for each patient in the given ward.
    """
    patients_in_ward = Patient.objects.filter(bed__ward=ward).select_related('bed')
    patient_vitals = []
    for patient in patients_in_ward:
        latest_vital = PatientVitals.objects.filter(patient=patient).order_by('-timestamp').first()
        if latest_vital:
            patient_vitals.append(latest_vital)
    return patient_vitals
def ward_details(request, ward_slug):
    ward = get_object_or_404(Ward, slug=ward_slug)
    latest_condition = WardReading.objects.filter(ward=ward).order_by('-timestamp').first()
    patient_vitals = get_patient_vitals_data(ward)

    context = {
        'ward_name': ward.name,
        'ward_slug': ward.slug,
        'latest_condition': latest_condition,
        "patient_vitals": patient_vitals,
    }

    return render(request, 'data_management/ward-details.html', context)





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


def htmx_ward_patient_vitals(request, ward_slug):
    """
    HTMX endpoint to return patient vitals for a specific ward
    """
    ward = get_object_or_404(Ward, slug=ward_slug)
    patient_vitals = get_patient_vitals_data(ward)

    context = {
        'patient_vitals': patient_vitals,
        'ward': ward,
    }

    return render(request, 'data_management/snippets/ward-patient-vitals.html', context)


def htmx_ward_status(request, ward_slug):
    """
    HTMX endpoint to return ward status (temperature, humidity, noise, light)
    """
    ward = get_object_or_404(Ward, slug=ward_slug)
    latest_condition = WardReading.objects.filter(ward=ward).order_by('-timestamp').first()

    context = {
        'latest_condition': latest_condition,
        'ward': ward,
    }

    return render(request, 'data_management/snippets/ward-status.html', context)


def ward_chart_data(request, ward_slug):
    """
    Returns historical temperature, humidity, and noise level data for a ward as JSON for Chart.js
    """
    ward = get_object_or_404(Ward, slug=ward_slug)

    # Get the last 24 hours of data (or last 20 readings if less than 24 hours)
    ward_readings = WardReading.objects.filter(ward=ward).order_by('-timestamp')[:20]
    ward_readings = list(reversed(ward_readings))  # Reverse to chronological order

    # Prepare data for Chart.js
    labels = []
    temperature_data = []
    humidity_data = []
    noise_data = []

    for reading in ward_readings:
        # Convert UTC timestamp to local timezone before formatting
        local_time = timezone.localtime(reading.timestamp)
        labels.append(local_time.strftime('%H:%M'))
        temperature_data.append(float(reading.temperature) if reading.temperature else 0)
        humidity_data.append(float(reading.humidity) if reading.humidity else 0)
        noise_data.append(float(reading.noise_level) if reading.noise_level else 0)

    # Prepare light intensity data
    light_intensity_data = []
    for reading in ward_readings:
        light_intensity_data.append(float(reading.light_intensity) if reading.light_intensity else 0)

    return JsonResponse({
        'labels': labels,
        'temperature': temperature_data,
        'humidity': humidity_data,
        'noise_level': noise_data,
        'light_intensity': light_intensity_data,
        'ward_name': ward.name
    })
