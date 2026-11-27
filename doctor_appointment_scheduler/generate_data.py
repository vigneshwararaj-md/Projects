import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

# Set random seed for reproducibility
np.random.seed(42)
random.seed(42)

# Number of appointments
n_appointments = 10000

# Generate patient IDs (some patients will have multiple appointments)
patient_ids = np.random.randint(1000, 9999, size=n_appointments)

# Generate appointment dates (last 12 months)
end_date = datetime(2025, 5, 31)
start_date = datetime(2024, 6, 1)
appointment_dates = [start_date + timedelta(days=random.randint(0, 364)) for _ in range(n_appointments)]

# Generate booking dates (1-30 days before appointment)
booking_dates = []
lead_times = []
for apt_date in appointment_dates:
    lead_time = random.randint(0, 30)  # days between booking and appointment
    lead_times.append(lead_time)
    booking_dates.append(apt_date - timedelta(days=lead_time))

# Generate patient demographics
ages = np.random.randint(18, 90, size=n_appointments)
gender = np.random.choice(['M', 'F'], size=n_appointments, p=[0.45, 0.55])
distance_km = np.random.exponential(scale=5, size=n_appointments)
distance_km = np.round(distance_km, 1)
distance_km = np.clip(distance_km, 0.5, 50)  # between 0.5 and 50 km

# Appointment time slots
time_slots = ['09:00', '10:00', '11:00', '12:00', '14:00', '15:00', '16:00', '17:00']
appointment_times = np.random.choice(time_slots, size=n_appointments, p=[0.15,0.15,0.15,0.1,0.15,0.1,0.1,0.1])

# Day of week
days_of_week = [apt_date.strftime('%A') for apt_date in appointment_dates]

# Departments
departments = ['Cardiology', 'Dermatology', 'Pediatrics', 'Orthopedics', 'Gynecology', 'Neurology', 'ENT', 'Ophthalmology']
department = np.random.choice(departments, size=n_appointments)

# Doctors (2 per department)
doctors_by_dept = {
    'Cardiology': ['Dr. Sharma', 'Dr. Patel'],
    'Dermatology': ['Dr. Verma', 'Dr. Nair'],
    'Pediatrics': ['Dr. Reddy', 'Dr. Kaur'],
    'Orthopedics': ['Dr. Singh', 'Dr. Joshi'],
    'Gynecology': ['Dr. Mehta', 'Dr. Gupta'],
    'Neurology': ['Dr. Kumar', 'Dr. Choudhary'],
    'ENT': ['Dr. Rao', 'Dr. Iyer'],
    'Ophthalmology': ['Dr. Menon', 'Dr. Bhat']
}
doctor = [random.choice(doctors_by_dept[dept]) for dept in department]

# Reminder status (0 = no reminder, 1 = SMS reminder, 2 = Email reminder, 3 = Both)
reminder_sent = np.random.choice([0, 1, 2, 3], size=n_appointments, p=[0.2, 0.4, 0.3, 0.1])

# Previous no-shows (0 to 5)
prior_no_shows = np.random.poisson(lam=0.5, size=n_appointments)
prior_no_shows = np.clip(prior_no_shows, 0, 5)

# Previous visits (0 to 20)
previous_visits = np.random.negative_binomial(2, 0.3, size=n_appointments)
previous_visits = np.clip(previous_visits, 0, 20)

# SMS opt-in
sms_opt_in = np.random.choice([0, 1], size=n_appointments, p=[0.2, 0.8])

# Calculate no-show probability based on features (realistic logic)
no_show_prob = []

for i in range(n_appointments):
    prob = 0.15  # base probability
    
    # Age factor (younger and older have higher no-show)
    if ages[i] < 25 or ages[i] > 70:
        prob += 0.1
    
    # Lead time factor (longer lead time = higher no-show)
    if lead_times[i] > 14:
        prob += 0.15
    elif lead_times[i] > 7:
        prob += 0.07
    
    # Distance factor
    if distance_km[i] > 15:
        prob += 0.12
    elif distance_km[i] > 8:
        prob += 0.06
    
    # Prior no-shows (strong predictor)
    prob += prior_no_shows[i] * 0.08
    
    # Reminder reduces no-show
    if reminder_sent[i] > 0:
        prob -= 0.08
    if reminder_sent[i] == 3:  # both reminders
        prob -= 0.05
    
    # Monday and Friday have higher no-show
    if days_of_week[i] in ['Monday', 'Friday']:
        prob += 0.05
    
    # Early morning and late afternoon better attendance
    if appointment_times[i] in ['09:00', '10:00', '16:00', '17:00']:
        prob -= 0.03
    
    # SMS opt-in helps
    if sms_opt_in[i] == 1:
        prob -= 0.04
    
    # Department variation
    if department[i] in ['Dermatology', 'ENT']:
        prob += 0.03
    
    prob = np.clip(prob, 0.05, 0.85)
    no_show_prob.append(prob)

# Generate actual no-show status (1 = no-show, 0 = showed up)
no_show = [1 if random.random() < prob else 0 for prob in no_show_prob]

# Create DataFrame
df = pd.DataFrame({
    'appointment_id': range(1, n_appointments + 1),
    'patient_id': patient_ids,
    'booking_date': booking_dates,
    'appointment_date': appointment_dates,
    'lead_time_days': lead_times,
    'age': ages,
    'gender': gender,
    'distance_km': distance_km,
    'appointment_time': appointment_times,
    'day_of_week': days_of_week,
    'department': department,
    'doctor': doctor,
    'reminder_status': reminder_sent,  # 0=None, 1=SMS, 2=Email, 3=Both
    'prior_no_shows': prior_no_shows,
    'previous_visits': previous_visits,
    'sms_opt_in': sms_opt_in,
    'no_show_probability': no_show_prob,
    'no_show': no_show  # Target variable
})

# Add derived features
df['weekend'] = df['day_of_week'].isin(['Saturday', 'Sunday']).astype(int)
df['season'] = df['appointment_date'].dt.month.apply(lambda m: 'Winter' if m in [12,1,2] else ('Spring' if m in [3,4,5] else ('Summer' if m in [6,7,8] else 'Fall')))

# Display basic info
print("Dataset created successfully!")
print(f"Shape: {df.shape}")
print(f"\nFirst 5 rows:")
print(df.head())
print(f"\nMissing values: {df.isnull().sum().sum()}")
print(f"\nNo-show distribution:")
print(df['no_show'].value_counts(normalize=True))
print(f"\nData types:")
print(df.dtypes)

# Save to CSV
df.to_csv('appointment_data.csv', index=False)
print("\n✅ Data saved to 'appointment_data.csv'")