from fastapi import APIRouter
from dags.tasks.training import train_outlier_models
from config import MODELS_TO_TRAIN

router = APIRouter()

class ModelTrainer:
    """
    A wrapper class to handle on-demand model training.
    """
    def run_training(self):
        """
        Calls the centralized training function.
        """
        print("On-demand model training triggered via API.")
        train_outlier_models(model_names=MODELS_TO_TRAIN)
        print("On-demand training process finished.")

@router.post("/train_models")
def trigger_model_training():
    """
    Triggers the outlier detection model training process on-demand.
    """
    try:
        trainer = ModelTrainer()
        trainer.run_training()
        return {"status": "success", "message": f"Model training initiated for: {MODELS_TO_TRAIN}"}
    except Exception as e:
        return {"status": "error", "message": f"An error occurred during model training: {e}"}
