import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
import pickle

# Load data
df = pd.read_csv('appointment_data.csv', parse_dates=['booking_date', 'appointment_date'])

print("=== Data Preprocessing ===")
print(f"Original shape: {df.shape}")

# Check missing values
print(f"\nMissing values:\n{df.isnull().sum()}")

# No missing values in our synthetic data, but handle if any
df = df.dropna()

# Feature engineering - additional features from PDF requirements
df['day_of_month'] = df['appointment_date'].dt.day
df['month'] = df['appointment_date'].dt.month
df['hour'] = pd.to_datetime(df['appointment_time'], format='%H:%M').dt.hour
df['is_morning'] = (df['hour'] < 12).astype(int)
df['is_weekend'] = df['day_of_week'].isin(['Saturday', 'Sunday']).astype(int)

# Visit frequency (previous visits + this one)
df['total_visits_including_current'] = df['previous_visits'] + 1

# High risk flag based on prior no-shows
df['has_prior_no_shows'] = (df['prior_no_shows'] > 0).astype(int)

# Long lead time flag
df['long_lead_time'] = (df['lead_time_days'] > 14).astype(int)

# Distance category
df['distance_category'] = pd.cut(df['distance_km'], bins=[0, 5, 10, 20, 100], labels=['Short', 'Medium', 'Long', 'Very Long'])

print(f"\nNew features added. Shape: {df.shape}")

# Encode categorical features
categorical_cols = ['gender', 'day_of_week', 'department', 'doctor', 'reminder_status', 
                    'sms_opt_in', 'season', 'distance_category', 'appointment_time']

label_encoders = {}
for col in categorical_cols:
    le = LabelEncoder()
    df[col + '_encoded'] = le.fit_transform(df[col])
    label_encoders[col] = le
    print(f"Encoded {col}: {dict(zip(le.classes_, le.transform(le.classes_)))}")

# Define features for model
feature_cols = [
    'lead_time_days', 'age', 'distance_km', 'prior_no_shows', 'previous_visits',
    'gender_encoded', 'day_of_week_encoded', 'department_encoded', 'doctor_encoded',
    'reminder_status_encoded', 'sms_opt_in_encoded', 'season_encoded',
    'hour', 'is_morning', 'is_weekend', 'has_prior_no_shows', 'long_lead_time',
    'distance_category_encoded'
]

# Add appointment_time_encoded
df['appointment_time_encoded'] = label_encoders['appointment_time'].transform(df['appointment_time'])
feature_cols.append('appointment_time_encoded')

# Prepare X and y
X = df[feature_cols]
y = df['no_show']

# Scale numerical features
numerical_cols = ['lead_time_days', 'age', 'distance_km', 'prior_no_shows', 'previous_visits', 'hour']
scaler = StandardScaler()
X[numerical_cols] = scaler.fit_transform(X[numerical_cols])

# Train-test split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

print(f"\n=== Dataset Split ===")
print(f"Training set: {X_train.shape}")
print(f"Test set: {X_test.shape}")
print(f"\nTraining no-show rate: {y_train.mean():.2%}")
print(f"Test no-show rate: {y_test.mean():.2%}")

# Save preprocessed data and encoders
df.to_csv('preprocessed_appointment_data.csv', index=False)
pd.DataFrame(X_train).to_csv('X_train.csv', index=False)
pd.DataFrame(X_test).to_csv('X_test.csv', index=False)
pd.DataFrame(y_train).to_csv('y_train.csv', index=False)
pd.DataFrame(y_test).to_csv('y_test.csv', index=False)

# Save encoders and scaler
with open('label_encoders.pkl', 'wb') as f:
    pickle.dump(label_encoders, f)
with open('scaler.pkl', 'wb') as f:
    pickle.dump(scaler, f)
with open('feature_cols.pkl', 'wb') as f:
    pickle.dump(feature_cols, f)

print("\n✅ Preprocessing complete. Files saved:")
print("  - preprocessed_appointment_data.csv")
print("  - X_train.csv, X_test.csv, y_train.csv, y_test.csv")
print("  - label_encoders.pkl, scaler.pkl, feature_cols.pkl")