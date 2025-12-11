# config.py
# Central configuration for the OutlierDetector project.

# Define the database path relative to the project root
DB_PATH = "outlier_detector.db"
DB_URI = f"sqlite:///{DB_PATH}"

# Define the rolling window size for feature engineering.
# Use pandas offset aliases: https://pandas.pydata.org/pandas-docs/stable/user_guide/timeseries.html#offset-aliases
FEATURE_WINDOW_INTERVAL = '5min'

# Define the list of anomaly detection models to train.
# An odd number is recommended to avoid ties in majority voting.
# See PyCaret documentation for available model IDs: https://pycaret.org/anomaly-detection/
MODELS_TO_TRAIN = ['lof', 'iforest', 'knn']
