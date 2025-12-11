from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime
import pandas as pd
from sqlalchemy import create_engine
from pycaret.anomaly import load_model, predict_model
from config import DB_URI, FEATURE_WINDOW_INTERVAL, MODELS_TO_TRAIN
from cachetools import TTLCache

router = APIRouter()

# --- Model Loading ---
models = {}

def _load_models_if_needed():
    if not models:
        print("Attempting to load models...")
        for model_name in MODELS_TO_TRAIN:
            if model_name not in models:
                model_path = f'outlier_model_{model_name}'
                try:
                    models[model_name] = load_model(model_path)
                    print(f"Successfully loaded model: {model_path}.pkl")
                except FileNotFoundError:
                    print(f"Info: Model file not found for '{model_name}'. It may not have been trained yet.")
                except Exception as e:
                    print(f"An error occurred loading model '{model_name}': {e}")
        if not models:
            print("Warning: No models could be loaded.")

def _reload_all_models():
    global models
    print("Initiating full model reload...")
    models = {}
    _load_models_if_needed()
    if not models:
        raise HTTPException(status_code=500, detail="Failed to load any models after reload attempt.")
    print("Model reload complete.")

_load_models_if_needed()

# --- Caching Setup ---
interval_seconds = pd.Timedelta(FEATURE_WINDOW_INTERVAL).total_seconds()
cache = TTLCache(maxsize=10000, ttl=interval_seconds + 60)

class LogEntry(BaseModel):
    timestamp: datetime
    ip_address: str
    service_endpoint: str
    http_response_code: int

def get_recent_logs_with_caching(ip_address: str, engine) -> pd.DataFrame:
    window_end = pd.Timestamp.now()
    window_start = window_end - pd.Timedelta(FEATURE_WINDOW_INTERVAL)

    if ip_address in cache:
        print(f"Cache HIT for IP: {ip_address}")
        cached_df = cache[ip_address]
        pruned_df = cached_df[cached_df['timestamp'] >= window_start].copy()
        cache[ip_address] = pruned_df
        return pruned_df
    
    print(f"Cache MISS for IP: {ip_address}. Querying database.")
    query = f"""
    SELECT timestamp, ip_address, service_endpoint, http_response_code 
    FROM logs 
    WHERE ip_address = '{ip_address}' AND timestamp BETWEEN '{window_start}' AND '{window_end}'
    """
    with engine.connect() as connection:
        recent_logs_df = pd.read_sql(query, connection, parse_dates=['timestamp'])
    
    cache[ip_address] = recent_logs_df
    return recent_logs_df

@router.post("/detect")
def detect_outlier(log_entry: LogEntry):
    _load_models_if_needed()
    
    if not models:
        raise HTTPException(status_code=500, detail="No models are loaded. Cannot perform detection. Please train the models first.")

    try:
        engine = create_engine(DB_URI)
        
        # Create a DataFrame from the input log entry, using its own timestamp
        new_log_df = pd.DataFrame([log_entry.model_dump()])
        
        # Insert the new log entry into the database
        with engine.connect() as connection:
            new_log_df.to_sql('logs', connection, if_exists='append', index=False)
        print(f"Inserted new log for IP: {log_entry.ip_address}")

        recent_logs_df = get_recent_logs_with_caching(log_entry.ip_address, engine)
        
        combined_df = pd.concat([recent_logs_df, new_log_df], ignore_index=True)
        # Ensure timestamp column is in the correct format before setting as index
        combined_df['timestamp'] = pd.to_datetime(combined_df['timestamp'])
        combined_df = combined_df.set_index('timestamp').sort_index()

        combined_df['client_error'] = ((combined_df['http_response_code'] >= 400) & (combined_df['http_response_code'] < 500)).astype(int)
        combined_df['server_error'] = ((combined_df['http_response_code'] >= 500) & (combined_df['http_response_code'] < 600)).astype(int)

        aggregations = { 'service_endpoint': 'count', 'client_error': 'sum', 'server_error': 'sum' }
        
        features_df = combined_df.rolling(FEATURE_WINDOW_INTERVAL).agg(aggregations)
        features_df.columns = ['request_count', 'client_error_count', 'server_error_count']
        
        latest_features = features_df.iloc[-1:].reset_index(drop=True)

        all_predictions = {}
        anomaly_votes = 0
        for name, model in models.items():
            prediction_df = predict_model(model, data=latest_features)
            is_anomaly = bool(prediction_df['Anomaly'].iloc[0])
            if is_anomaly:
                anomaly_votes += 1
            all_predictions[name] = { "is_anomaly": is_anomaly, "score": str(prediction_df['Anomaly_Score'].iloc[0]) }

        final_is_anomaly = anomaly_votes >= (len(models) / 2)

        cache[log_entry.ip_address] = combined_df.reset_index()

        return {
            "status": "success",
            "log_entry": log_entry.model_dump(),
            "final_decision": { "is_anomaly": final_is_anomaly, "reason": f"{anomaly_votes} out of {len(models)} models flagged it as an anomaly." },
            "model_predictions": all_predictions,
            "features_calculated": latest_features.to_dict(orient='records')[0]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/reload_models")
def reload_models_endpoint():
    try:
        _reload_all_models()
        return {"status": "success", "message": "Models reloaded successfully."}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred during model reload: {e}")
