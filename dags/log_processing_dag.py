from airflow.decorators import dag, task
from pendulum import datetime
from dags.tasks.processing import process_log_data_from_db
from dags.tasks.training import train_outlier_models
from config import MODELS_TO_TRAIN

@dag(
    dag_id='log_feature_engineering_and_training_pipeline',
    start_date=datetime(2025, 12, 5, tz="UTC"),
    schedule_interval='@daily',
    catchup=False,
    tags=['ml', 'feature-engineering', 'training', 'database'],
)
def log_processing_and_training_dag():
    """
    A DAG to process log data, generate features, and train multiple outlier detection models.
    """

    @task
    def run_feature_engineering_from_db():
        """
        This task runs the main feature engineering logic.
        """
        process_log_data_from_db()

    @task
    def run_model_training():
        """
        This task trains multiple outlier detection models on the newly generated features.
        """
        print(f"Starting training for models: {MODELS_TO_TRAIN}")
        train_outlier_models(model_names=MODELS_TO_TRAIN)

    # Define the task dependency
    run_feature_engineering_from_db() >> run_model_training()

# Instantiate the DAG
log_processing_and_training_dag()
