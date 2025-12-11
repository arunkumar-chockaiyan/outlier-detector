import pandas as pd
from sqlalchemy import create_engine
from config import DB_URI, FEATURE_WINDOW_INTERVAL

def process_log_data_from_db():
    """
    Loads log data from the 'logs' table, generates features over a
    configurable sliding window, and saves the result to the 'features' table.
    """
    print("Connecting to the database...")
    try:
        engine = create_engine(DB_URI)
        
        # Read data from the 'logs' table
        print("Reading data from 'logs' table...")
        df = pd.read_sql_table('logs', engine)

        # Convert timestamp and set as index
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.set_index('timestamp').sort_index()

        # Create helper columns for error types
        df['client_error'] = ((df['http_response_code'] >= 400) & (df['http_response_code'] < 500)).astype(int)
        df['server_error'] = ((df['http_response_code'] >= 500) & (df['http_response_code'] < 600)).astype(int)

        # Define aggregations
        aggregations = {
            'service_endpoint': 'count',
            'client_error': 'sum',
            'server_error': 'sum'
        }

        # Group by IP and apply rolling aggregations using the configurable window
        print(f"Generating features with a '{FEATURE_WINDOW_INTERVAL}' rolling window...")
        features_df = df.groupby('ip_address').rolling(FEATURE_WINDOW_INTERVAL).agg(aggregations)

        # Clean up column names and reset index
        features_df.columns = ['request_count', 'client_error_count', 'server_error_count']
        features_df = features_df.reset_index()

        # Save the features to the 'features' table
        print("Saving features to 'features' table...")
        features_df.to_sql('features', engine, if_exists='replace', index=False)
        
        print("Processing complete.")

    except Exception as e:
        print(f"An error occurred: {e}")
        raise
