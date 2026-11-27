import pickle
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path

class NoShowPredictor:
    def __init__(self):
        model_path = Path(__file__).parent / 'no_show_model.pkl'
        encoders_path = Path(__file__).parent / 'label_encoders.pkl'
        scaler_path = Path(__file__).parent / 'scaler.pkl'
        features_path = Path(__file__).parent / 'feature_cols.pkl'
        
        with open(model_path, 'rb') as f:
            self.model = pickle.load(f)
        with open(encoders_path, 'rb') as f:
            self.label_encoders = pickle.load(f)
        with open(scaler_path, 'rb') as f:
            self.scaler = pickle.load(f)
        with open(features_path, 'rb') as f:
            self.feature_cols = pickle.load(f)
    
    def predict_risk(self, patient_data):
        """
        patient_data: dict with keys:
        - age, gender, distance_km, prior_no_shows, previous_visits,
        - appointment_time, day_of_week, department, doctor, 
        - lead_time_days, sms_opt_in
        """
        # Create DataFrame with one row
        df = pd.DataFrame([patient_data])
        
        # Encode categorical variables
        for col, encoder in self.label_encoders.items():
            if col in df.columns:
                df[col + '_encoded'] = encoder.transform(df[col])
            elif col == 'reminder_status':
                # Default to no reminder
                df['reminder_status_encoded'] = 0
        
        # Add derived features
        df['hour'] = pd.to_datetime(df['appointment_time'], format='%H:%M:%S').dt.hour
        df['is_morning'] = (df['hour'] < 12).astype(int)
        df['is_weekend'] = df['day_of_week'].isin(['Saturday', 'Sunday']).astype(int)
        df['has_prior_no_shows'] = (df['prior_no_shows'] > 0).astype(int)
        df['long_lead_time'] = (df['lead_time_days'] > 14).astype(int)
        
        # Distance category
        df['distance_category'] = pd.cut(df['distance_km'], 
                                          bins=[0, 5, 10, 20, 100], 
                                          labels=['Short', 'Medium', 'Long', 'Very Long'])
        df['distance_category_encoded'] = self.label_encoders['distance_category'].transform(df['distance_category'])
        
        # Season
        df['season'] = 'Winter'  # default
        df['season_encoded'] = self.label_encoders['season'].transform(['Winter'])[0]
        
        # Prepare feature vector
        X = df[self.feature_cols].copy()
        
        # Scale numerical features
        numerical_cols = ['lead_time_days', 'age', 'distance_km', 'prior_no_shows', 'previous_visits', 'hour']
        X[numerical_cols] = self.scaler.transform(X[numerical_cols])
        
        # Predict
        risk_score = self.model.predict_proba(X)[0][1]
        
        # Determine risk level
        if risk_score < 0.3:
            risk_level = "Low"
        elif risk_score < 0.5:
            risk_level = "Medium"
        elif risk_score < 0.7:
            risk_level = "High"
        else:
            risk_level = "Very High"
        
        return {
            'risk_score': round(risk_score * 100, 1),
            'risk_level': risk_level,
            'recommendation': self._get_recommendation(risk_level)
        }
    
    def _get_recommendation(self, risk_level):
        recommendations = {
            'Low': "Standard reminder via SMS/Email is sufficient",
            'Medium': "Send reminder 3 days and 1 day before appointment",
            'High': "Send multiple reminders + consider confirmation call",
            'Very High': "Requires confirmation call 2 days before, consider rescheduling"
        }
        return recommendations.get(risk_level, "Send standard reminder")

# Singleton instance
predictor = NoShowPredictor()