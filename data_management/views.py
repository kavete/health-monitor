from django.shortcuts import get_object_or_404, render
from .models import Ward, Patient, Doctor, Microcontroller, Bed, WardReading, PatientVitals
from django.db.models import Max

def dashboard(request):
    ward_count = Ward.objects.count()
    patient_count = Patient.objects.count()
    doctor_count = Doctor.objects.count()
    bed_count = Bed.objects.count()
    microcontroller_count = Microcontroller.objects.count()

    latest_per_ward = (
        WardReading.objects.values('ward')
        .annotate(latest=Max('timestamp'))
    )
    # Build a list of latest WardCondition objects for each ward
    latest_conditions = [
        WardReading.objects.filter(ward=entry['ward'], timestamp=entry['latest']).first()
        for entry in latest_per_ward
    ]
    context = {
        'ward_conditions': latest_conditions,
        'ward_count': ward_count,
        'patient_count': patient_count,
        'doctor_count': doctor_count,
        'bed_count': bed_count,
        'microcontroller_count': microcontroller_count,
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
