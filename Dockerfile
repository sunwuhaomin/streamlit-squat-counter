# Use the official lightweight Python image.
# https://hub.docker.com/_/python
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    && apt-get clean

# Install pip requirements
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy the application files
COPY . /app
WORKDIR /app

# Expose the port Streamlit is running on
EXPOSE 8501

# Run Streamlit
CMD ["streamlit", "run", "streamlit-squat-counter-saveuploadvideo.py"]