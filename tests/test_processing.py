import pytest
import pandas as pd
from sqlalchemy import create_engine
from dags.tasks.processing import process_log_data_from_db
from unittest.mock import patch

@pytest.fixture
def setup_test_database():
    """
    Fixture to set up an in-memory SQLite database with sample log data for testing.
    This ensures that tests do not interfere with the development database.
    """
    engine = create_engine("sqlite:///:memory:")
    
    logs_data = {
        'timestamp': [
            '2023-01-01 10:00:10', '2023-01-01 10:00:20', '2023-01-01 10:00:30',
            '2023-01-01 10:00:40', '2023-01-01 10:00:50'
        ],
        'ip_address': ['192.168.1.1', '192.168.1.1', '192.168.1.1', '192.168.1.2', '192.168.1.1'],
        'service_endpoint': ['/home', '/api', '/home', '/login', '/api'],
        'http_response_code': [200, 404, 500, 200, 401]
    }
    logs_df = pd.DataFrame(logs_data)
    logs_df['timestamp'] = pd.to_datetime(logs_df['timestamp'])
    
    logs_df.to_sql('logs', engine, index=False)
    
    return engine

def test_process_log_data_from_db(setup_test_database):
    """
    Tests the core feature engineering logic.
    It checks if the aggregations (request_count, client_error_count, server_error_count)
    are calculated correctly over a rolling window.
    """
    test_engine = setup_test_database
    
    # Patch the 'create_engine' call within the 'processing' module.
    # Force it to return the engine we already created and populated in our fixture.
    with patch('dags.tasks.processing.create_engine', return_value=test_engine):
        # Now, when this function calls create_engine, it will get our test_engine.
        process_log_data_from_db()

    # Read the results from the 'features' table in our test database
    features_df = pd.read_sql_table('features', test_engine)
    
    # --- Assertions ---
    expected_columns = ['ip_address', 'timestamp', 'request_count', 'client_error_count', 'server_error_count']
    assert all(col in features_df.columns for col in expected_columns)
    
    # Check the calculations for the last entry of IP '192.168.1.1'
    # At 10:00:50, the 5min window for this IP includes 4 requests.
    final_entry_ip1 = features_df[features_df['ip_address'] == '192.168.1.1'].iloc[-1]
    
    assert final_entry_ip1['request_count'] == 4
    assert final_entry_ip1['client_error_count'] == 2
    assert final_entry_ip1['server_error_count'] == 1

    # Check the calculations for IP '192.168.1.2'
    entry_ip2 = features_df[features_df['ip_address'] == '192.168.1.2'].iloc[0]
    assert entry_ip2['request_count'] == 1
    assert entry_ip2['client_error_count'] == 0
    assert entry_ip2['server_error_count'] == 0
    
    print("test_process_log_data_from_db passed successfully.")
