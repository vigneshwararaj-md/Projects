from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class PatientProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=15)
    date_of_birth = models.DateField(null=True, blank=True)
    address = models.TextField(blank=True)
    prior_no_shows = models.IntegerField(default=0)
    previous_visits = models.IntegerField(default=0)
    sms_opt_in = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.user.get_full_name()} - Patient"

class DoctorProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    specialization = models.CharField(max_length=100)
    license_number = models.CharField(max_length=50)
    phone = models.CharField(max_length=15)
    available_days = models.CharField(max_length=200, help_text="Comma-separated days")
    
    def __str__(self):
        return f"Dr. {self.user.last_name} - {self.specialization}"

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        PatientProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'patientprofile'):
        instance.patientprofile.save()