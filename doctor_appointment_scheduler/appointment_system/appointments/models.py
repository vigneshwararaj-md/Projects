from django.db import models
from django.contrib.auth.models import User
from accounts.models import PatientProfile, DoctorProfile
from datetime import date, timedelta

class Appointment(models.Model):
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('no_show', 'No-Show'),
    ]
    
    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE)
    doctor = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE)
    appointment_date = models.DateField()
    appointment_time = models.TimeField()
    department = models.CharField(max_length=100)
    booking_date = models.DateTimeField(auto_now_add=True)
    lead_time_days = models.IntegerField(editable=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    risk_score = models.FloatField(default=0.0, help_text="No-show risk probability")
    reminder_sent = models.BooleanField(default=False)
    reminder_type = models.CharField(max_length=20, blank=True, null=True)
    notes = models.TextField(blank=True)
    
    def save(self, *args, **kwargs):
        if not self.pk:  # New appointment
            self.lead_time_days = (self.appointment_date - date.today()).days
            if self.lead_time_days < 0:
                self.lead_time_days = 0
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.patient.user.get_full_name()} with Dr. {self.doctor.user.last_name} on {self.appointment_date}"