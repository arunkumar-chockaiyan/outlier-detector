# --- Stage 1: Build Stage ---
# Use a full Python image to build the environment, which may require build tools.
FROM python:3.9-slim as builder

# Set the working directory
WORKDIR /app

# Install poetry - a modern dependency manager (can also use pip)
# Using poetry or pip-tools is a best practice for creating locked dependencies.
# For now, we'll stick with pip and requirements.txt for simplicity.
COPY requirements.txt .

# Create a virtual environment inside the container
RUN python -m venv /opt/venv
# Activate the virtual environment and install dependencies
RUN . /opt/venv/bin/activate && pip install --no-cache-dir -r requirements.txt

# --- Stage 2: Final Stage ---
# Use a slim Python image for the final application to reduce size.
FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Copy the virtual environment from the builder stage
COPY --from=builder /opt/venv /opt/venv

# Copy the application source code
COPY . .

# Activate the virtual environment for subsequent commands
ENV PATH="/opt/venv/bin:$PATH"

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application
# Use --host 0.0.0.0 to make it accessible from outside the container.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
