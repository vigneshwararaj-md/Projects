from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import datetime, date
from .models import Appointment
from accounts.models import PatientProfile, DoctorProfile
from predictor.risk_predictor import predictor

def home(request):
    return render(request, 'home.html')

@login_required
def dashboard(request):
    # Get user's appointments
    patient_profile = request.user.patientprofile
    upcoming_appointments = Appointment.objects.filter(
        patient=patient_profile,
        appointment_date__gte=date.today(),
        status='scheduled'
    ).order_by('appointment_date', 'appointment_time')
    
    past_appointments = Appointment.objects.filter(
        patient=patient_profile,
        appointment_date__lt=date.today()
    ).order_by('-appointment_date')[:10]
    
    # Calculate stats
    total_appointments = Appointment.objects.filter(patient=patient_profile).count()
    no_shows = Appointment.objects.filter(patient=patient_profile, status='no_show').count()
    no_show_rate = (no_shows / total_appointments * 100) if total_appointments > 0 else 0
    
    context = {
        'upcoming_appointments': upcoming_appointments,
        'past_appointments': past_appointments,
        'total_appointments': total_appointments,
        'no_show_rate': round(no_show_rate, 1),
        'no_shows': no_shows,
    }
    return render(request, 'appointments/dashboard.html', context)

@login_required
def book_appointment(request):
    if request.method == 'POST':
        # Get form data
        doctor_id = request.POST.get('doctor')
        appointment_date = datetime.strptime(request.POST.get('appointment_date'), '%Y-%m-%d').date()
        appointment_time = request.POST.get('appointment_time')
        department = request.POST.get('department')
        notes = request.POST.get('notes', '')
        
        # Get patient profile
        patient = request.user.patientprofile
        doctor = get_object_or_404(DoctorProfile, id=doctor_id)
        
        # Calculate lead time
        lead_time_days = (appointment_date - date.today()).days
        if lead_time_days < 0:
            lead_time_days = 0
        
        # Format doctor name as expected by the model (e.g., "Dr. Sharma")
        doctor_name = f"Dr. {doctor.user.last_name}"
        
        # Get day of week
        day_of_week = appointment_date.strftime('%A')
        
        # Prepare data for risk prediction - FORMAT MATCHES TRAINING DATA
        patient_data = {
            'age': calculate_age(request.user.patientprofile.date_of_birth) if request.user.patientprofile.date_of_birth else 35,
            'gender': request.POST.get('gender', 'M'),
            'distance_km': float(request.POST.get('distance_km', 5.0)),
            'prior_no_shows': patient.prior_no_shows,
            'previous_visits': patient.previous_visits,
            'appointment_time': appointment_time,
            'day_of_week': day_of_week,
            'department': department,
            'doctor': doctor_name,  # Fixed: Use "Dr. Sharma" format
            'lead_time_days': lead_time_days,
            'sms_opt_in': patient.sms_opt_in
        }
        
        # Get risk prediction
        try:
            from predictor.risk_predictor import predictor
            risk_result = predictor.predict_risk(patient_data)
            risk_score = risk_result['risk_score']
        except Exception as e:
            print(f"Prediction error: {e}")
            # Default risk score if prediction fails
            risk_score = 30.0
        
        # Create appointment
        appointment = Appointment.objects.create(
            patient=patient,
            doctor=doctor,
            appointment_date=appointment_date,
            appointment_time=appointment_time,
            department=department,
            risk_score=risk_score,
            notes=notes,
            status='scheduled'
        )
        
        messages.success(request, f'Appointment booked! Risk Score: {risk_score}%')
        
        # Show warning for high risk
        if risk_score >= 50:
            messages.warning(request, f'⚠️ High risk of no-show ({risk_score}%). Please send reminders or confirm before appointment.')
        else:
            messages.info(request, f'Risk score: {risk_score}% - Standard reminder will be sent.')
        
        return redirect('my_appointments')
    
    # GET request - show booking form
    doctors = DoctorProfile.objects.all()
    departments = ['Cardiology', 'Dermatology', 'Pediatrics', 'Orthopedics', 
                   'Gynecology', 'Neurology', 'ENT', 'Ophthalmology']
    time_slots = ['09:00', '10:00', '11:00', '12:00', '14:00', '15:00', '16:00', '17:00']
    
    context = {
        'doctors': doctors,
        'departments': departments,
        'time_slots': time_slots,
    }
    return render(request, 'appointments/book_appointment.html', context)

@login_required
def my_appointments(request):
    patient = request.user.patientprofile
    appointments = Appointment.objects.filter(patient=patient).order_by('-appointment_date', '-appointment_time')
    
    for apt in appointments:
        if apt.risk_score < 30:
            apt.risk_level = 'Low'
        elif apt.risk_score < 50:
            apt.risk_level = 'Medium'
        elif apt.risk_score < 70:
            apt.risk_level = 'High'
        else:
            apt.risk_level = 'Very High'
    
    return render(request, 'appointments/my_appointments.html', {'appointments': appointments})

@login_required
def cancel_appointment(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id, patient=request.user.patientprofile)
    
    if request.method == 'POST':
        appointment.status = 'cancelled'
        appointment.save()
        messages.success(request, 'Appointment cancelled successfully.')
        return redirect('my_appointments')
    
    return render(request, 'appointments/cancel_appointment.html', {'appointment': appointment})

def calculate_age(birth_date):
    if not birth_date:
        return 30
    today = date.today()
    return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))