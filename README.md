# Real-Time Log Anomaly Detection System

This project provides a complete end-to-end system for detecting anomalies in log data in real-time. It includes services for data generation, a scheduled pipeline for feature engineering and model training, and a live API endpoint for inference.

The system is built with a modern Python stack, leveraging FastAPI for the API, Apache Airflow for orchestration, and PyCaret for rapid machine learning model development.

> **Note:** This project was developed with significant assistance from Gemini Code Assist, an AI-powered collaborator in the IDE.

## Core Features

- **Real-Time Detection API**: An endpoint that takes a single log entry and predicts if it's an anomaly using an ensemble of trained models.
- **Automated Training Pipeline**: An Apache Airflow DAG that runs on a daily schedule to process new data, generate features, and retrain the ML models.
- **On-Demand Services**: All major functions (data generation, feature processing, model training) are also exposed as API endpoints for manual control and testing.
- **Ensemble Modeling**: Uses multiple anomaly detection models (LOF, Isolation Forest, KNN) and a majority vote for robust and reliable predictions.
- **Configurable Feature Engineering**: Easily configure the time window for rolling features (e.g., `5min`, `1h`) in a central config file.
- **Performant Caching**: An in-memory TTL cache is used to minimize database load during real-time detection.
- **Automated Model Reloading**: The inference service automatically reloads the latest models after the Airflow training pipeline completes, ensuring predictions are always made with the freshest models.

---

## Getting Started

You can run this project in two ways:
1.  **Using Docker (Recommended)**: Easiest way to get started. Manages all dependencies within a container.
2.  **Local Setup with Conda**: For local development and debugging.

---

## Option 1: Running with Docker (Recommended)

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running.

### Step 1: Build the Docker Image

From the project's root directory, run the `docker build` command. This will create an image named `outlier-detector-app`.

```sh
docker build -t outlier-detector-app .
```

### Step 2: Run the Docker Container

Run the container, mapping port 8000 on your local machine to port 8000 inside the container. We also use a volume (`-v`) to persist the database and model files on your local machine.

```sh
docker run -d -p 8000:8000 \
  -v $(pwd)/outlier_detector.db:/app/outlier_detector.db \
  -v $(pwd)/outlier_model_lof.pkl:/app/outlier_model_lof.pkl \
  -v $(pwd)/outlier_model_iforest.pkl:/app/outlier_model_iforest.pkl \
  -v $(pwd)/outlier_model_knn.pkl:/app/outlier_model_knn.pkl \
  --name outlier-detector-container \
  outlier-detector-app
```
*Note for Windows users: Replace `$(pwd)` with `%cd%` if you are using Command Prompt.*

The application is now running inside the container. You can interact with it at `http://127.0.0.1:8000`.

### Step 3: Use the API

You can now follow the [Manual Workflow](#manual-workflow-using-the-api) steps (e.g., using `curl`) to generate data, train models, and detect anomalies. The data and models will be saved to your local project directory.

---

## Option 2: Local Setup with Conda

### Prerequisites
- **Conda**: It is highly recommended to install [Miniconda](https://docs.conda.io/projects/miniconda/en/latest/).

### Installation Steps
1.  **Clone the repository:**
    ```sh
    git clone https://github.com/arunkumar-chockaiyan/outlier-detector.git
    cd outlier-detector
    ```
2.  **Create & Activate Conda Environment:**
    ```sh
    conda create -n od_env python=3.9
    conda activate od_env
    ```
3.  **Install Dependencies:**
    ```sh
    pip install -r requirements.txt
    ```

### Manual Workflow (Using the API)
This workflow is ideal for development, testing, and on-demand actions.

#### Step 1: Start the FastAPI Server
```sh
uvicorn app.main:app --reload
```
The API is now available at `http://127.0.0.1:8000`. Access the interactive docs at `http://127.0.0.1:8000/docs`.

#### Step 2: Generate Sample Data
```sh
curl -X POST http://127.0.0.1:8000/data/generate_sample
```

#### Step 3: Train the Models
```sh
curl -X POST http://127.0.0.1:8000/model/train_models
```

#### Step 4: Detect an Anomaly
```sh
curl -X POST -H "Content-Type: application/json" \
-d '{
  "timestamp": "2023-10-27T10:00:00Z",
  "ip_address": "10.0.0.5",
  "service_endpoint": "/admin",
  "http_response_code": 500
}' \
http://127.0.0.1:8000/outlier/detect
```

---

## Automated Workflow (Using Apache Airflow)

This workflow is for automated, scheduled retraining of the models and runs on your local machine (not in the Docker container).

### Step 1: Initialize Airflow
```sh
export AIRFLOW_HOME="$(pwd)"
airflow db init
airflow users create --username admin --password admin --firstname Anonymous --lastname User --role Admin --email admin@example.com
```

### Step 2: Run Airflow
Run the webserver and scheduler in two separate terminals.
- **Terminal 1:** `airflow webserver --port 8080`
- **Terminal 2:** `airflow scheduler`

### Step 3: Use the Airflow UI
1.  Open your browser to `http://localhost:8080`.
2.  Un-pause the `log_feature_engineering_and_training_pipeline` DAG.
3.  The DAG will run on its schedule (`@daily`) or can be triggered manually. After training, it will automatically notify the running API service (whether local or in Docker) to reload the new models.

---

## Running the Tests

This project uses `pytest` for unit testing.
```sh
pytest -v
```
