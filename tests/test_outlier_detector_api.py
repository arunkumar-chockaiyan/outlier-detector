import pytest
from fastapi.testclient import TestClient
from app.main import app  # Import the main FastAPI app
from unittest.mock import patch, MagicMock
import pandas as pd

# Create a TestClient instance that will be used in all tests
client = TestClient(app)

@pytest.fixture
def mock_pycaret_predict():
    """
    Fixture to mock the 'predict_model' function from PyCaret.
    This prevents the test from needing a real model file.
    """
    mock_prediction = pd.DataFrame({
        'Anomaly': [1],
        'Anomaly_Score': [0.678]
    })
    with patch('app.services.outlier_detector.predict_model', return_value=mock_prediction) as mock:
        yield mock

@pytest.fixture
def mock_db_and_cache():
    """
    Fixture to mock database interactions and the cache.
    This isolates the API endpoint logic from the database and cache layers.
    """
    with patch('app.services.outlier_detector.create_engine') as mock_engine, \
         patch('app.services.outlier_detector.get_recent_logs_with_caching', return_value=pd.DataFrame()) as mock_cache:
        yield mock_engine, mock_cache

def test_detect_outlier_endpoint(mock_pycaret_predict, mock_db_and_cache):
    """
    Tests the /outlier/detect endpoint.
    It verifies that the endpoint correctly processes a valid log entry,
    calls the prediction model, and returns the expected response structure.
    """
    # Mock the loaded models dictionary to simulate that models are ready
    with patch('app.services.outlier_detector.models', {'lof': MagicMock(), 'iforest': MagicMock()}):
        
        log_payload = {
            "timestamp": "2023-10-27T10:00:00Z",
            "ip_address": "192.168.1.50",
            "service_endpoint": "/api/v1/data",
            "http_response_code": 404
        }
        
        response = client.post("/outlier/detect", json=log_payload)
        
        assert response.status_code == 200
        
        response_data = response.json()
        assert response_data['status'] == 'success'
        assert response_data['final_decision']['is_anomaly'] is True
        assert 'model_predictions' in response_data
        assert 'lof' in response_data['model_predictions']
        assert response_data['model_predictions']['lof']['score'] == '0.678'

def test_detect_outlier_no_models_loaded(mock_db_and_cache):
    """
    Tests the behavior of the /outlier/detect endpoint when no models can be loaded.
    It should return a specific error message.
    """
    # Patch the models dictionary to be empty AND patch the loading function
    # to prevent it from trying to load models from disk during the test.
    with patch('app.services.outlier_detector.models', {}), \
         patch('app.services.outlier_detector._load_models_if_needed'):
        
        log_payload = {
            "timestamp": "2023-10-27T10:00:00Z",
            "ip_address": "192.168.1.50",
            "service_endpoint": "/api/v1/data",
            "http_response_code": 200
        }
        
        response = client.post("/outlier/detect", json=log_payload)
        
        # Assert that the response indicates an error because the models dict remains empty
        assert response.status_code == 500
        assert "No models are loaded" in response.json()['detail']

# To run these tests:
# 1. Navigate to your project root in the terminal.
# 2. Run the command: pytest
