from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from .risk_predictor import predictor
from appointments.models import Appointment
from accounts.models import PatientProfile

@login_required
def test_predictor(request):
    risk_result = None
    if request.method == 'POST':
        patient_data = {
            'age': int(request.POST.get('age')),
            'gender': request.POST.get('gender'),
            'distance_km': float(request.POST.get('distance_km')),
            'prior_no_shows': int(request.POST.get('prior_no_shows')),
            'previous_visits': int(request.POST.get('previous_visits')),
            'appointment_time': request.POST.get('appointment_time'),
            'day_of_week': request.POST.get('day_of_week'),
            'department': request.POST.get('department'),
            'doctor': request.POST.get('doctor'),
            'lead_time_days': int(request.POST.get('lead_time_days')),
            'sms_opt_in': request.POST.get('sms_opt_in') == 'on'
        }
        risk_result = predictor.predict_risk(patient_data)
    
    return render(request, 'predictor/test.html', {'risk_result': risk_result})

@staff_member_required
def dashboard_stats(request):
    total_appointments = Appointment.objects.count()
    high_risk_appointments = Appointment.objects.filter(risk_score__gte=50).count()
    no_show_rate = (Appointment.objects.filter(status='no_show').count() / total_appointments * 100) if total_appointments > 0 else 0
    
    context = {
        'total_appointments': total_appointments,
        'high_risk_appointments': high_risk_appointments,
        'no_show_rate': round(no_show_rate, 1)
    }
    return render(request, 'predictor/stats.html', context)