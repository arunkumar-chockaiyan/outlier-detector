from fastapi import FastAPI
from app.services import sample_data_generator, data_processor, model_trainer, outlier_detector

app = FastAPI(
    title="Outlier Detector API",
    description="An API for generating data, training anomaly detection models, and detecting outliers in real-time.",
    version="1.0.0"
)

# Include the routers from each service module
app.include_router(sample_data_generator.router, prefix="/data", tags=["Data Generation"])
app.include_router(data_processor.router, prefix="/features", tags=["Feature Generation"])
app.include_router(model_trainer.router, prefix="/model", tags=["Model Training"])
app.include_router(outlier_detector.router, prefix="/outlier", tags=["Outlier Detection"])

@app.get("/", tags=["Root"])
def read_root():
    """
    Root endpoint for the API.
    """
    return {"message": "Welcome to the Outlier Detector API"}
