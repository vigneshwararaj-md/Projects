import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from xgboost import XGBClassifier
from sklearn.metrics import (accuracy_score, precision_score, recall_score, 
                             f1_score, roc_auc_score, confusion_matrix,
                             classification_report)
import matplotlib.pyplot as plt
import seaborn as sns
import pickle
import warnings
warnings.filterwarnings('ignore')

# Load data
X_train = pd.read_csv('X_train.csv')
X_test = pd.read_csv('X_test.csv')
y_train = pd.read_csv('y_train.csv').values.ravel()
y_test = pd.read_csv('y_test.csv').values.ravel()

print("=== Model Training & Evaluation ===")
print(f"Training samples: {len(X_train)}")
print(f"Test samples: {len(X_test)}")

# Initialize models
models = {
    'Logistic Regression': LogisticRegression(max_iter=1000, random_state=42),
    'Random Forest': RandomForestClassifier(n_estimators=100, random_state=42),
    'XGBoost': XGBClassifier(n_estimators=100, learning_rate=0.1, random_state=42)
}

# Train and evaluate each model
results = {}
best_model = None
best_auc = 0

for name, model in models.items():
    print(f"\n{'='*50}")
    print(f"Training {name}...")
    
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    y_pred_proba = model.predict_proba(X_test)[:, 1]
    
    # Calculate metrics
    accuracy = accuracy_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred)
    recall = recall_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)
    roc_auc = roc_auc_score(y_test, y_pred_proba)
    
    results[name] = {
        'Accuracy': accuracy,
        'Precision': precision,
        'Recall': recall,
        'F1-Score': f1,
        'ROC-AUC': roc_auc,
        'model': model
    }
    
    print(f"Accuracy: {accuracy:.4f}")
    print(f"Precision: {precision:.4f}")
    print(f"Recall: {recall:.4f}")
    print(f"F1-Score: {f1:.4f}")
    print(f"ROC-AUC: {roc_auc:.4f}")
    
    if roc_auc > best_auc:
        best_auc = roc_auc
        best_model = model
        best_model_name = name

print(f"\n{'='*50}")
print(f"🏆 Best Model: {best_model_name} with ROC-AUC = {best_auc:.4f}")

# Save best model
with open('no_show_model.pkl', 'wb') as f:
    pickle.dump(best_model, f)

print("✅ Best model saved to 'no_show_model.pkl'")

# Confusion Matrix for best model
y_pred_best = best_model.predict(X_test)
cm = confusion_matrix(y_test, y_pred_best)

plt.figure(figsize=(8, 6))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
            xticklabels=['Showed Up', 'No-Show'],
            yticklabels=['Showed Up', 'No-Show'])
plt.title(f'Confusion Matrix - {best_model_name}')
plt.xlabel('Predicted')
plt.ylabel('Actual')
plt.tight_layout()
plt.savefig('confusion_matrix.png', dpi=100, bbox_inches='tight')
plt.show()

# Feature Importance (for Random Forest or XGBoost)
feature_cols = pd.read_pickle('feature_cols.pkl')

if hasattr(best_model, 'feature_importances_'):
    importances = best_model.feature_importances_
    feature_importance_df = pd.DataFrame({
        'Feature': feature_cols,
        'Importance': importances
    }).sort_values('Importance', ascending=False)
    
    print(f"\n=== Top 10 Feature Importances ({best_model_name}) ===")
    print(feature_importance_df.head(10))
    
    # Plot
    plt.figure(figsize=(10, 8))
    sns.barplot(data=feature_importance_df.head(10), x='Importance', y='Feature')
    plt.title(f'Top 10 Feature Importances - {best_model_name}')
    plt.tight_layout()
    plt.savefig('feature_importance.png', dpi=100, bbox_inches='tight')
    plt.show()

# Classification Report
print(f"\n=== Detailed Classification Report ({best_model_name}) ===")
print(classification_report(y_test, y_pred_best, target_names=['Showed Up', 'No-Show']))

# Save results summary
results_df = pd.DataFrame(results).T
results_df.to_csv('model_results.csv')
print("\n✅ Results saved to 'model_results.csv'")