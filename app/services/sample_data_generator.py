import pandas as pd
import numpy as np
from fastapi import APIRouter
from sqlalchemy import create_engine
from config import DB_PATH, DB_URI

router = APIRouter()

class SampleDataGenerator:
    def generate_log_data(self, num_rows=300000):
        print("Generating sample log data...")
        ips = [f"192.168.1.{i}" for i in range(1, 20)] + ["10.0.0.5"]
        endpoints = ["/home", "/login", "/api/data", "/profile", "/logout", "/admin"]
        responses = [200, 201, 404, 401, 500, 302]

        start_time = pd.Timestamp.now() - pd.Timedelta(days=1)

        data = {
            "timestamp": pd.to_datetime(start_time) + pd.to_timedelta(
                np.random.randint(0, 60 * 60 * 24, size=num_rows), unit='s'),
            "ip_address": np.random.choice(ips, size=num_rows, p=[0.05] * 19 + [0.05]),
            "service_endpoint": np.random.choice(endpoints, size=num_rows),
            "http_response_code": np.random.choice(responses, size=num_rows, p=[0.7, 0.1, 0.1, 0.05, 0.03, 0.02])
        }
        return pd.DataFrame(data)

@router.post("/generate_sample")
def generate_sample():
    """
    Generates sample log data and saves it to the 'logs' table in the SQLite database.
    """
    try:
        engine = create_engine(DB_URI)
        generator = SampleDataGenerator()
        df = generator.generate_log_data()

        df.to_sql('logs', engine, if_exists='append', index=False)
        
        num_rows = len(df)
        return {"message": f"{num_rows} rows of sample data saved to the 'logs' table in {DB_PATH}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
