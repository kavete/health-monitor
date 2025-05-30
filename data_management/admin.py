from django.contrib import admin
from django.core.exceptions import ValidationError
from django.forms import ModelForm
from .models import Microcontroller, Ward, Bed, Doctor, Patient, WardReading, PatientVitals
from django.db.models import Q
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser
from django.utils.text import slugify


class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Role', {'fields': ('is_doctor', 'is_patient')}),
    )

admin.site.register(CustomUser, CustomUserAdmin)
# Optional: restrict microcontroller choices in forms
class BedAdminForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance.pk:
            current_microcontroller = self.instance.microcontroller
            allowed_microcontrollers = Microcontroller.objects.filter(
                Q(assigned_bed__isnull=True),
                Q(assigned_ward__isnull=True) | Q(ward=self.instance.ward)
            ) | Microcontroller.objects.filter(pk=current_microcontroller.pk if current_microcontroller else None)
        else:
            allowed_microcontrollers = Microcontroller.objects.filter(
                assigned_bed__isnull=True,
                assigned_ward__isnull=True
            )

        self.fields['microcontroller'].queryset = allowed_microcontrollers


class WardAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'microcontroller')
    prepopulated_fields = {"slug": ("name",)}

    def save_model(self, request, obj, form, change):
        obj.full_clean()
        super().save_model(request, obj, form, change)


class BedAdmin(admin.ModelAdmin):
    form = BedAdminForm
    list_display = ["ward", "bed_number" ,"microcontroller"]
    search_fields = ["ward", "microcontroller"]
    list_filter = ["ward"]

    
    def save_model(self, request, obj, form, change):
        obj.full_clean()
        super().save_model(request, obj, form, change)

 

class MicrocontrollerAdmin(admin.ModelAdmin):
    list_display = ('identifier', 'name', 'ward', 'bed')
    exclude = ('identifier',)
    # prepopulated_fields = {"identifier": ("name",)}  # will fill initially but you override in clean

    # Optional: make identifier readonly to prevent manual changes
    # readonly_fields = ('identifier',)
class PatientAdminForm(ModelForm):
    class Meta:
        model = Patient
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from .models import Bed, Patient
        assigned_bed_pks = Patient.objects.exclude(pk=self.instance.pk).values_list('bed_id', flat=True)
        if self.instance.pk and self.instance.bed:
            allowed_beds = Bed.objects.filter(pk=self.instance.bed.pk) | Bed.objects.exclude(pk__in=assigned_bed_pks)
        else:
            allowed_beds = Bed.objects.exclude(pk__in=assigned_bed_pks)
        # Only filter by ward if ward is set on the instance
        if getattr(self.instance, 'ward_id', None):
            allowed_beds = allowed_beds.filter(ward=self.instance.ward)
        self.fields['bed'].queryset = allowed_beds.distinct()


class PatientAdmin(admin.ModelAdmin):
    form = PatientAdminForm
    list_display = ['get_username', 'ward', 'bed', 'get_microcontroller']
    search_fields = ['user__username']
    autocomplete_fields = ['user']
    list_filter = ['ward']

    def get_username(self, obj):
        return obj.user.username
    get_username.short_description = 'Name'

    def get_microcontroller(self, obj):
        # Use the microcontroller property you added on Patient
        return obj.microcontroller.identifier if obj.microcontroller else "-"
    get_microcontroller.short_description = 'Microcontroller'
    get_microcontroller.admin_order_field = 'bed__microcontroller__identifier'


class DoctorAdmin(admin.ModelAdmin):
    list_display = ['get_username', 'specialization']
    search_fields = ['user__username', 'specialization']

    def get_username(self, obj):
        return obj.user.username
    get_username.short_description = 'Name'


class WardReadingAdmin(admin.ModelAdmin):
    list_display = ['ward', 'temperature', 'humidity', 'noise_level']
    list_filter = ["ward"]
    search_fields =["ward__name"]
    ordering = ["-timestamp"]

class PatientVitalsAdmin(admin.ModelAdmin):
    list_display = ["patient", "temperature", "heart_rate", "oxygen_saturation", "timestamp"]
    list_filter = ["patient"]
    search_fields= ["patient__user__username"]
    ordering = ["-timestamp"]


admin.site.register(Microcontroller, MicrocontrollerAdmin)
admin.site.register(Ward, WardAdmin)
admin.site.register(Bed, BedAdmin)
admin.site.register(Doctor, DoctorAdmin)
admin.site.register(Patient, PatientAdmin)
admin.site.register(PatientVitals, PatientVitalsAdmin)
admin.site.register(WardReading, WardReadingAdmin)
