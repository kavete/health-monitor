from data_management.models import Bed


beds = Bed.objects.filter(ward_id=1).filter(patient__isnull=True)
print(beds)