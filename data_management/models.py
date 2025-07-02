from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth.models import AbstractUser
from django.utils.text import slugify

class Microcontroller(models.Model):
    name = models.CharField(max_length=100)
    identifier = models.SlugField(max_length=100, unique=True, blank=True)  # Allow blank to generate in save
    ward = models.ForeignKey(
        'Ward',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='microcontrollers',
        help_text="Set this only if the microcontroller is assigned for ward readings."
    )

    def __str__(self):
        return str(self.identifier)

    def clean(self):
        if self.identifier:
            qs = Microcontroller.objects.exclude(pk=self.pk).filter(identifier=self.identifier)
            if qs.exists():
                raise ValidationError({'identifier': 'Identifier must be unique.'})

    def save(self, *args, **kwargs):
        if not self.identifier:
            base_slug = slugify(self.name)
            existing_slugs = Microcontroller.objects.filter(identifier__startswith=base_slug).values_list('identifier', flat=True)

            if base_slug not in existing_slugs:
                self.identifier = base_slug
            else:
                counter = 2
                while f"{base_slug}-{counter}" in existing_slugs:
                    counter += 1
                self.identifier = f"{base_slug}-{counter}"

        super().save(*args, **kwargs)

    @property
    def bed(self):
        """
        Returns the bed this microcontroller is assigned to, if any.
        """
        try:
            return self.assigned_bed
        except (AttributeError, Bed.DoesNotExist):
            return None

class Ward(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=60, unique=True)
    description = models.TextField(max_length=500, null=True, blank=True)
    location = models.CharField(max_length=100, null=True, blank=True)
    microcontroller = models.OneToOneField(
        Microcontroller,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_ward'
    )

    def __str__(self):
        return f"Ward {self.name} ({self.location})" if self.location else str(self.name)



    def clean(self):
        if self.microcontroller:
            if Bed.objects.filter(microcontroller=self.microcontroller).exists():
                raise ValidationError(f"Microcontroller {self.microcontroller} is already assigned to a bed.")
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)



class Bed(models.Model):
    ward = models.ForeignKey(Ward, on_delete=models.CASCADE, related_name="beds")
    bed_number = models.IntegerField()
    microcontroller = models.OneToOneField(
        Microcontroller,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_bed'
    )
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["ward", "bed_number"], name="unique_bed_per_ward")
        ]

    def clean(self):
        if self.microcontroller:
            if Ward.objects.filter(microcontroller=self.microcontroller).exists():
                raise ValidationError(f"Microcontroller {self.microcontroller} is already assigned to a ward.")
            if self.microcontroller.ward and self.microcontroller.ward != self.ward:
                raise ValidationError(f"Microcontroller {self.microcontroller} is assigned to {self.microcontroller.ward}, not to this bed's ward {self.ward}.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


    def __str__(self):
        return f"{self.bed_number} in {self.ward}"


class CustomUser(AbstractUser):
    is_doctor = models.BooleanField(default=False)
    is_patient = models.BooleanField(default=False)
    email = models.EmailField(unique=True, blank=True, null=True)


    def __str__(self):
        return self.username


class Patient(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, primary_key=True)
    ward = models.ForeignKey(Ward, on_delete=models.CASCADE, related_name='patients')
    bed = models.OneToOneField(Bed, on_delete=models.SET_NULL, related_name="patient", null=True, blank=True)
    first_admission_date = models.DateField(auto_now_add=True)
    national_id = models.IntegerField(unique=True, null=True, blank=True, help_text="National ID or equivalent identification number")

    @property
    def microcontroller(self):
        # Return microcontroller assigned to the patient's bed if bed exists, else None
        if self.bed and hasattr(self.bed, "microcontroller"):
            return self.bed.microcontroller
        return None

    def clean(self):
        # Ensure bed is in same ward
        if self.bed and self.bed.ward != self.ward:
            raise ValidationError(f"Assigned bed {self.bed} belongs to ward {self.bed.ward}, not {self.ward}.")

    def save(self, *args, **kwargs):
        self.full_clean()  # This calls the clean() method and field validation
        super().save(*args, **kwargs)

    def __str__(self):
        name = self.user.get_full_name() if self.user and hasattr(self.user, "get_full_name") else (self.user.username if self.user and hasattr(self.user, "username") else "")
        if self.bed and hasattr(self.bed, "bed_number"):
            return f"{name} - {self.ward} Bed: {self.bed.bed_number}"
        return f"{name} - {self.ward} (No Bed Assigned)"



class Doctor(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, primary_key=True)
    specialization = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    patients = models.ManyToManyField('Patient', related_name='doctors', blank=True)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        name = self.user.get_full_name() if self.user and hasattr(self.user, "get_full_name") else (self.user.username if self.user and hasattr(self.user, "username") else "")
        return f"Dr. {name}"


class WardReading(models.Model):
    ward = models.ForeignKey(Ward, on_delete=models.CASCADE)
    temperature = models.FloatField()
    humidity = models.FloatField()
    noise_level = models.FloatField()
    light_intensity = models.FloatField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Ward Readings"
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.ward} {self.timestamp}"


class PatientVitals(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    temperature = models.FloatField()
    heart_rate = models.IntegerField()
    oxygen_saturation = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Patient Vitals"
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.patient} @ {self.timestamp}"
