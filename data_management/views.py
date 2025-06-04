from django.shortcuts import get_object_or_404, render
from .models import Ward, Patient, Doctor, Microcontroller, Bed, WardReading, PatientVitals
from django.db.models import Max
from django.utils.timezone import now


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


def dashboard(request):
    stats= get_dashboard_stats()
    latest_conditions = get_latest_ward_conditions()
    context = {
        'ward_conditions': latest_conditions,
        **stats,
    }
    return render(request, 'data_management/index.html', context)


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
