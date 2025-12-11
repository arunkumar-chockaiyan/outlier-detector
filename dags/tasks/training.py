import pandas as pd
from sqlalchemy import create_engine
from pycaret.anomaly import setup, create_model, save_model
from config import DB_URI, MODELS_TO_TRAIN
import os
import requests

# The URL for the running outlier detection service
DETECTION_SERVICE_URL = "http://127.0.0.1:8000"

def train_outlier_models(model_names: list = MODELS_TO_TRAIN):
    """
    Trains multiple outlier detection models and then triggers a reload
    in the running detection service.
    """
    print("Connecting to the database for model training...")
    try:
        engine = create_engine(DB_URI)
        
        print("Reading features from the database...")
        features_df = pd.read_sql_table('features', engine, parse_dates=['timestamp'])

        twenty_four_hours_ago = pd.Timestamp.now() - pd.Timedelta(days=1)
        recent_features = features_df[features_df['timestamp'] >= twenty_four_hours_ago]

        if recent_features.empty:
            print("No recent features found in the last 24 hours. Skipping training.")
            return

        numeric_features = recent_features.select_dtypes(include=['number'])
        
        print(f"Setting up PyCaret anomaly detection experiment with {len(recent_features)} records...")
        setup(data=numeric_features, verbose=False)

        for model_name in model_names:
            print(f"--- Training {model_name} model ---")
            model = create_model(model_name)
            
            model_path = f'outlier_model_{model_name}'
            print(f"Saving the trained model to {model_path}.pkl")
            save_model(model, model_path)

        print("All model training and saving complete.")
        
        # --- Trigger Model Reload ---
        print("Triggering model reload in the detection service...")
        try:
            reload_url = f"{DETECTION_SERVICE_URL}/outlier/reload_models"
            response = requests.post(reload_url, timeout=30)
            response.raise_for_status() # Raises an exception for 4xx or 5xx status codes
            print(f"Successfully triggered model reload: {response.json()}")
        except requests.exceptions.RequestException as e:
            print(f"Error: Could not trigger model reload in the detection service. Is it running? Details: {e}")
            # We don't re-raise this exception, as the training itself was successful.
            # This is a notification failure, not a pipeline failure.

    except Exception as e:
        print(f"An error occurred during model training: {e}")
        raise
