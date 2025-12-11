from fastapi import APIRouter
from dags.tasks.processing import process_log_data_from_db

router = APIRouter()

@router.post("/generate_features")
def generate_features():
    """
    Triggers the feature generation process on-demand.
    """
    try:
        print("On-demand feature generation triggered via API.")
        process_log_data_from_db()
        return {"status": "success", "message": "Feature generation task completed successfully."}
    except Exception as e:
        return {"status": "error", "message": f"An error occurred during feature generation: {e}"}
